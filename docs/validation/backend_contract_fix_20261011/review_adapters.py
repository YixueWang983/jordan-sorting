import __main__ as contract
import unittest

def skip():
    raise unittest.SkipTest("synthetic skipped adapter")

class BrokenAfterSplit(contract.OrderedListModel):
    has_split = False
    def split_value(self, handle, value):
        result = super().split_value(handle, value)
        self.has_split = True
        return result
    def insert_boundary(self, item, anchor_id, side):
        if self.has_split:
            raise RuntimeError("synthetic defect: insertion disabled after split")
        return super().insert_boundary(item, anchor_id, side)
