"""Path-local split machinery for the heterogeneous representation.

Search races the two fingers. Only a selected rib component is temporarily
oriented downwards; its split path is dismantled and joined by black height.
The large remainder stays heterogeneous and uses deletion-shortness repair.
No member enumeration, whole-tree conversion, or output-size traversal occurs.
"""

from functools import wraps

from heterogeneous_finger_backend import ExternalLeaf, InternalNode, _Tracked, ROOT, INTERIOR
from sibling_list_backend import LEFT, RIGHT


def phase(name):
    def decorate(method):
        @wraps(method)
        def call(self, *args, **kwargs):
            with self.b.work.phase(name):
                return method(self, *args, **kwargs)
        return call
    return decorate


class RootedPiece(_Tracked):
    __slots__ = ("root", "size", "maximum")
    _fields = frozenset(__slots__)
    _pointers = frozenset(("root",))
    _kind = "fragment"

    def __init__(self, ledger, root, size, maximum):
        self._ledger = ledger
        ledger.allocate("fragment")
        self.root, self.size, self.maximum = root, size, maximum


class FingerPiece(_Tracked):
    __slots__ = ("root", "size", "left_top", "right_top", "left_finger", "right_finger")
    _fields = frozenset(__slots__)
    _pointers = _fields - {"size"}
    _kind = "fragment"

    def __init__(self, ledger, root, size):
        self._ledger = ledger
        ledger.allocate("fragment")
        self.root, self.size = root, size
        self.left_top = self.right_top = None
        self.left_finger = self.right_finger = None


class TreeOperations:
    def __init__(self, backend):
        self.b = backend

    @staticmethod
    def opposite(side):
        return RIGHT if side == LEFT else LEFT

    def retire(self, node):
        if not isinstance(node, InternalNode):
            raise RuntimeError("split must not retire an external leaf")
        del self.b._nodes[node.node_id]
        self.b.work.add("registry_writes")
        self.b.work.add("node_retirements")

    def color_rank(self, node, red):
        if node.red != red:
            node.rank += -1 if red else 1
            self.b._color(node, red)

    def refresh_down(self, node):
        if isinstance(node, InternalNode):
            node.span = node.left.span + node.right.span
            node.rank = node.left.rank + (not node.red)

    def rotate_down(self, node, side):
        """Ordinary local rotation INSIDE a detached, downward component."""
        self.b.work.add("rotations")
        if side == LEFT:
            self.b.work.add("left_rotations")
            promoted = node.right
            node.right = promoted.left
            promoted.left = node
        else:
            self.b.work.add("right_rotations")
            promoted = node.left
            node.left = promoted.right
            promoted.right = node
        self.refresh_down(node)
        self.refresh_down(promoted)
        return promoted

    @phase("rebalance")
    def balance_down(self, node):
        # Four black/red/red cases; unlike endpoint insertion this helper also
        # handles inner rotations. Recolored root may propagate up the join path.
        if not node.red:
            if node.left.red and node.left.left.red:
                self.b.work.add("join_outer_repairs")
                node = self.rotate_down(node, RIGHT)
            elif node.left.red and node.left.right.red:
                self.b.work.add("join_inner_repairs")
                node.left = self.rotate_down(node.left, LEFT)
                node = self.rotate_down(node, RIGHT)
            elif node.right.red and node.right.right.red:
                self.b.work.add("join_outer_repairs")
                node = self.rotate_down(node, LEFT)
            elif node.right.red and node.right.left.red:
                self.b.work.add("join_inner_repairs")
                node.right = self.rotate_down(node.right, RIGHT)
                node = self.rotate_down(node, LEFT)
            else:
                self.refresh_down(node)
                return node
            self.b._color(node, True)
            self.b._color(node.left, False)
            self.b._color(node.right, False)
            self.refresh_down(node.left)
            self.refresh_down(node.right)
        self.refresh_down(node)
        return node

    @phase("join")
    def join_down(self, left, right, connector):
        self.b.work.add("join_calls")
        if left is None or right is None:
            self.retire(connector)
            return right if left is None else left
        self.color_rank(left.root, False)
        self.color_rank(right.root, False)
        connector.role = INTERIOR
        connector.key = left.maximum

        def combine(a, b):
            self.b.work.add("rooted_join_steps")
            if a.rank == b.rank and not a.red and not b.red:
                connector.left, connector.right = a, b
                self.b._color(connector, True)
                self.refresh_down(connector)
                return connector
            if a.rank > b.rank or (a.rank == b.rank and a.red):
                a.right = combine(a.right, b)
                return self.balance_down(a)
            b.left = combine(a, b.left)
            return self.balance_down(b)

        root = combine(left.root, right.root)
        self.color_rank(root, False)
        return RootedPiece(self.b.work, root, left.size + right.size, right.maximum)

    @phase("detach")
    def unreverse(self, finger, top, side):
        """Unreverse only nodes BELOW top; leave top to the caller."""
        node, below = finger, None
        while node is not top:
            self.b.work.add("rib_steps")
            above = self.b._up(node, side)
            if isinstance(node, ExternalLeaf):
                node.left = node.right = None
            else:
                self.b._set_up(node, below, side)  # slot now means outward CHILD
                self.refresh_down(node)
            node.role = INTERIOR
            below, node = node, above
        return below

    @phase("detach")
    def rooted_component(self, header, side, top, size, maximum):
        if isinstance(top, ExternalLeaf):
            top.left = top.right = None
        elif top.role == ROOT:
            left = self.unreverse(header.left_finger, top, LEFT)
            right = self.unreverse(header.right_finger, top, RIGHT)
            top.left, top.right = left, right
        else:
            below = self.unreverse(header.left_finger if side == LEFT else header.right_finger, top, side)
            self.b._set_up(top, below, side)
        top.role = INTERIOR
        top.span = size
        return RootedPiece(self.b.work, top, size, maximum)

    @phase("detach")
    def expose(self, root, parent, side):
        """Reverse one downward extremal path, returning its existing leaf."""
        node = root
        while True:
            self.b.work.add("rib_steps")
            leaf = isinstance(node, ExternalLeaf)
            below = None if leaf else (node.left if side == LEFT else node.right)
            if not leaf:
                node.span = (node.right if side == LEFT else node.left).span
            node.role = side
            self.b._set_up(node, parent, side)
            if leaf:
                return node
            parent, node = node, below

    @phase("detach")
    def fingers(self, piece):
        if piece is None:
            return None
        root = piece.root
        self.color_rank(root, False)
        result = FingerPiece(self.b.work, root, piece.size)
        if isinstance(root, ExternalLeaf):
            result.left_finger = result.right_finger = root
            root.role = ROOT
        else:
            left, right = root.left, root.right
            result.left_top, result.right_top = left, right
            result.left_finger = self.expose(left, root, LEFT)
            result.right_finger = self.expose(right, root, RIGHT)
            root.role, root.span = ROOT, 0
        root.left = root.right = None
        return result

    @phase("search")
    def locate_component(self, header, value):
        positions = {LEFT: (header.left_finger, 1), RIGHT: (header.right_finger, 1)}
        while True:
            for side in (LEFT, RIGHT):
                node, size = positions[side]
                self.b.work.add("search_steps")
                if node.role == ROOT:
                    return side, node, header.size
                parent = self.b._up(node, side)
                stop = (not self.b._less(parent.key, value) if side == LEFT
                        else not self.b._less(value, parent.key))
                if stop:
                    return side, node, size
                size = header.size if parent.role == ROOT else size + parent.span
                positions[side] = (parent, size)

    @phase("detach")
    def split_down(self, piece, value):
        node, maximum = piece.root, piece.maximum
        frames = []
        while isinstance(node, InternalNode):
            self.b.work.add("path_frames")
            with self.b.work.phase("search"):
                self.b.work.add("search_steps")
                go_left = self.b._less(value, node.key)
            if go_left:
                frames.append((node, LEFT, RootedPiece(self.b.work, node.right, node.right.span, maximum)))
                node, maximum = node.left, node.key
            else:
                frames.append((node, RIGHT, RootedPiece(self.b.work, node.left, node.left.span, node.key)))
                node = node.right
        with self.b.work.phase("search"):
            self.b.work.add("leaf_checks")
            is_left = not self.b._less(value, node.key)
        leaf = RootedPiece(self.b.work, node, 1, node.key)
        left, right = (leaf, None) if is_left else (None, leaf)
        for connector, direction, other in reversed(frames):
            if direction == LEFT:
                right = self.join_down(right, other, connector)
            else:
                left = self.join_down(other, left, connector)
        return left, right

    def rib_child(self, header, node, side):
        """A root-side deletion rotation may need the opposite rib's child.

        This is an explicit rib walk, charged to repair, NOT an O(1) query.
        It is never a traversal of the leaves of the opposite subtree.
        """
        current = header.left_finger if side == LEFT else header.right_finger
        while self.b._up(current, side) is not node:
            self.b.work.add("rib_steps")
            current = self.b._up(current, side)
        return current

    def sibling_children(self, header, sibling, side):
        near = sibling.left if side == LEFT else sibling.right
        if sibling.role == INTERIOR:
            far = sibling.right if side == LEFT else sibling.left
        else:
            far = self.rib_child(header, sibling, self.opposite(side))
        return near, far

    def rotate_short_parent(self, header, parent, sibling, short, near, far, side):
        """Rotate toward the short side; sibling moves onto that rib or root."""
        was_root = parent.role == ROOT
        above = None if was_root else self.b._up(parent, side)
        self.b.work.add("rotations")
        self.b.work.add("left_rotations" if side == LEFT else "right_rotations")
        parent.role = side
        self.b._set_up(parent, sibling, side)
        self.b._set_inner(parent, near, side)
        parent.span = near.span
        parent.rank = near.rank + (not parent.red)
        if was_root:
            sibling.role, sibling.left, sibling.right, sibling.span = ROOT, None, None, 0
            header.root = sibling
            if side == LEFT:
                header.left_top, header.right_top = parent, far
            else:
                header.left_top, header.right_top = far, parent
        else:
            sibling.role = side
            self.b._set_up(sibling, above, side)
            self.b._set_inner(sibling, far, side)
            sibling.span = far.span
            if above.role == ROOT:
                if side == LEFT:
                    header.left_top = sibling
                else:
                    header.right_top = sibling
        sibling.rank = far.rank + (not sibling.red)
        # short still points up to parent; far already has the correct reverse
        # parent if it is on the opposite global rib.

    def rotate_near(self, header, parent, sibling, near, side):
        self.b.work.add("deletion_near_rotations")
        self.color_rank(near, False)
        self.color_rank(sibling, True)
        if sibling.role == INTERIOR:
            promoted = self.rotate_down(sibling, RIGHT if side == LEFT else LEFT)
            self.b._set_inner(parent, promoted, side)
        else:
            opposite = self.opposite(side)
            inner = near.left if side == LEFT else near.right
            middle = near.right if side == LEFT else near.left
            self.b.work.add("rotations")
            self.b.work.add("right_rotations" if side == LEFT else "left_rotations")
            self.b._set_inner(sibling, middle, opposite)
            self.b._set_up(sibling, near, opposite)
            sibling.span = middle.span
            sibling.rank = middle.rank  # recolored red
            near.role = opposite
            self.b._set_inner(near, inner, opposite)
            self.b._set_up(near, parent, opposite)
            near.span, near.rank = inner.span, inner.rank + 1
            if side == LEFT:
                header.right_top = near
            else:
                header.left_top = near

    @phase("rebalance")
    def repair_short(self, header, short, side):
        while short.role != ROOT:
            self.b.work.add("deletion_fix_steps")
            parent = self.b._up(short, side)
            sibling = self.b._inner(parent, header, side)
            near, far = self.sibling_children(header, sibling, side)
            if sibling.red:
                self.b.work.add("deletion_red_sibling")
                self.color_rank(sibling, False)
                self.color_rank(parent, True)
                self.rotate_short_parent(header, parent, sibling, short, near, far, side)
                sibling = self.b._inner(parent, header, side)
                near, far = self.sibling_children(header, sibling, side)
            if not near.red and not far.red:
                self.b.work.add("deletion_propagations")
                self.color_rank(sibling, True)
                if parent.red:
                    self.b._color(parent, False)
                    parent.rank = sibling.rank + 1
                    return
                parent.rank -= 1
                short = parent
                continue
            if not far.red:
                self.rotate_near(header, parent, sibling, near, side)
                sibling = self.b._inner(parent, header, side)
                near, far = self.sibling_children(header, sibling, side)
            self.b.work.add("deletion_far_rotations")
            self.b._color(sibling, parent.red)
            self.b._color(parent, False)
            self.color_rank(far, False)
            self.rotate_short_parent(header, parent, sibling, short, near, far, side)
            return

    @phase("detach")
    def detach(self, header, side, top, size):
        """Remove a complete extremal component, preserving the large rest."""
        total = header.size
        maximum = header.right_finger.key
        if top.role == ROOT:
            return self.rooted_component(header, side, top, size, maximum), None, None
        parent = self.b._up(top, side)
        top_max = parent.key if side == LEFT else maximum
        sibling = self.b._inner(parent, header, side)
        was_root = parent.role == ROOT
        above = None if was_root else self.b._up(parent, side)
        parent_was_red = parent.red
        component = self.rooted_component(header, side, top, size, top_max)
        if was_root:
            rest_max = maximum if side == LEFT else parent.key
            rest = self.rooted_component(header, self.opposite(side), sibling, total-size, rest_max)
            return component, self.fingers(rest), parent
        # The sibling is an untouched inward subtree with a FULL span.
        new_finger = self.expose(sibling, above, side)
        header.size = total-size
        if side == LEFT:
            header.left_finger = new_finger
            if above.role == ROOT:
                header.left_top = sibling
        else:
            header.right_finger = new_finger
            if above.role == ROOT:
                header.right_top = sibling
        if not parent_was_red:
            if sibling.red:
                self.color_rank(sibling, False)
            else:
                self.repair_short(header, sibling, side)
        return component, header, parent

    @phase("join")
    def join_fingers(self, left, right, connector):
        self.b.work.add("join_calls")
        if left is None or right is None:
            self.retire(connector)
            return right if left is None else left
        side = LEFT if left.root.rank <= right.root.rank else RIGHT
        small, big = (left, right) if side == LEFT else (right, left)
        rank = small.root.rank
        target = big.left_finger if side == LEFT else big.right_finger
        size = 1
        while target.red or target.rank != rank:
            self.b.work.add("rib_steps")
            target = self.b._up(target, side)
            size = big.size if target.role == ROOT else size + target.span
        was_root = target.role == ROOT
        above = None if was_root else self.b._up(target, side)
        target_max = (big.right_finger.key if side == RIGHT or was_root else above.key)
        inside = self.rooted_component(big, side, target, size, target_max)
        outside = self.rooted_component(small, side, small.root, small.size, small.right_finger.key)
        if was_root:
            joined = self.join_down(outside, inside, connector) if side == LEFT else self.join_down(inside, outside, connector)
            return self.fingers(joined)
        connector.role = side
        connector.key = outside.maximum if side == LEFT else inside.maximum
        self.b._color(connector, True)
        connector.rank, connector.span = rank, inside.size
        self.b._set_up(connector, above, side)
        self.b._set_inner(connector, inside.root, side)
        finger = self.expose(outside.root, connector, side)
        if side == LEFT:
            big.left_finger = finger
            if above.role == ROOT:
                big.left_top = connector
        else:
            big.right_finger = finger
            if above.role == ROOT:
                big.right_top = connector
        big.size += outside.size
        with self.b.work.phase("rebalance"):
            # Valid reuse ONLY here: a new red connector with black equal-rank
            # children was inserted on the outer rib. Deletion and interior
            # join repairs above do not use the endpoint-insertion routine.
            self.b._repair_insert(big, connector, side)
        return big

    def split(self, header, value):
        self.b.work.add("split_calls")
        with self.b.work.phase("search"):
            self.b.work.add("leaf_checks", 2)
            if self.b._less(value, header.left_finger.key):
                return None, header
            if not self.b._less(value, header.right_finger.key):
                return header, None
        side, top, size = self.locate_component(header, value)
        component, rest, connector = self.detach(header, side, top, size)
        left, right = self.split_down(component, value)
        left, right = self.fingers(left), self.fingers(right)
        if rest is not None:
            if side == LEFT:
                right = self.join_fingers(right, rest, connector)
            else:
                left = self.join_fingers(rest, left, connector)
        return left, right
