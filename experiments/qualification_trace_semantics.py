"""Read-only trace predicates, independent of production state/trace validators.

Checks recorded list-size/owner transitions, event shape/order, simple input
geometry and reconstructible metrics. Does not decode or prove physical trees.
"""
import sys
if sys.flags.optimize != 0:
    raise RuntimeError('Trace evidence requires optimization level 0')
from collections import Counter
from committed_records import canonical


def require(ok, message):
    if not ok: raise ValueError('trace: '+message)


def positive(value): return type(value) is int and value > 0


def same(actual, expected, message):
    require(canonical(actual) == canonical(expected), message)


def check_trace(values, trace, metrics, backend):
    n=len(values)
    require(type(trace) is list and len(trace)==2+7*(n-3), 'event count')
    require(type(metrics) is dict and all(type(v) is int and v>=0 for v in metrics.values()), 'metrics types')
    names=('predecessor_accesses','successor_accesses','boundary_pair_checks','sibling_scan_checks',
        'sibling_lists_created','sibling_list_insertions','sibling_list_splits','split_items_scanned',
        'split_items_copied','split_items_transferred','output_insertions','z1_boundary_adjustments',
        'z1_output_anchor_adjustments','invariant_checks','trace_event_count')
    require(set(metrics)==set(names),'metrics fields')
    same(trace[0],dict(step='initialize_partial_order',processed_count=3,
        point_ids=sorted(range(1,4),key=lambda p:values[p-1])),'initial point order')
    initial=trace[1]
    require(type(initial) is dict and set(initial)=={'step','upper_pair_id','lower_pair_id','upper_list_id','lower_list_id'},'initial family fields')
    require(positive(initial['upper_list_id']) and positive(initial['lower_list_id'])
            and initial['upper_list_id']!=initial['lower_list_id'],'initial lists')
    same(initial,dict(step='initialize_pair_families',upper_pair_id=2,lower_pair_id=3,
         upper_list_id=initial['upper_list_id'],lower_list_id=initial['lower_list_id']),'initial families')
    live={initial['upper_list_id']:(-1,1),initial['lower_list_id']:(-2,1)}
    # Allocation identities last for the entire trace. Retirement removes a
    # live header, not its history; end insertion alone preserves its ID.
    seen_ids=set(live)
    calculated=Counter(dict.fromkeys(names,0));calculated['invariant_checks']=n-2;calculated['trace_event_count']=len(trace)
    splits=[]; observations=[]
    def pair_ok(pid,i,family):
        return type(pid) is int and (pid==(-1 if family=='upper' else -2) or 2<=pid<i and pid%2==i%2)
    def encloses(pid,point):
        return pid<0 or min(values[pid-2:pid])<values[point-1]<max(values[pid-2:pid])
    for i in range(4,n+1):
        family='upper' if i%2==0 else 'lower';increasing=values[i-2]<values[i-1]
        orientation='increasing' if increasing else 'decreasing'; events=trace[2+7*(i-4):2+7*(i-3)]
        require(all(type(e) is dict for e in events),'event objects')
        order=sorted(range(1,i),key=lambda p:values[p-1]);pos=order.index(i-1)
        selections=[]
        for offset,delta,label,metric in ((0,-1,'step1','predecessor_accesses'),(2,1,'step2','successor_accesses')):
            at=pos+delta;neighbor=order[at] if 0<=at<len(order) else None
            adjusted=i%2==1 and neighbor==1
            if adjusted:
                at+=delta;neighbor=order[at] if 0<=at<len(order) else None
            dummy=neighbor is None
            pid=(-1 if family=='upper' else -2) if dummy else neighbor if neighbor%2==i%2 else neighbor+1
            same(events[offset],dict(step=label+('_find_predecessor' if delta<0 else '_find_successor'),
                iteration=i,family=family,previous_point_id=i-1,neighbor_point_id=neighbor,adjusted_for_z1=adjusted),'neighbor event/order')
            same(events[offset+1],dict(step=label+'_select_boundary_pair',iteration=i,family=family,
                neighbor_point_id=neighbor,selected_pair_id=pid,used_dummy_pair=dummy,adjusted_for_z1=adjusted),'boundary event/order')
            selections.append(pid);calculated[metric]+=1+adjusted
            calculated['boundary_pair_checks']+=not dummy;calculated['z1_boundary_adjustments']+=adjusted
        a,b,c=events[4:];base=dict(iteration=i,family=family,orientation=orientation,pair_id=i)
        require(set(a)=={'step',*base,'boundary_pair_id','insertion_mode','parent_pair_id','sibling_list_id'},'insertion fields')
        boundary=selections[0 if increasing else 1];mode='singleton_list' if encloses(boundary,i-1) else 'boundary_insertion'
        owner=a['parent_pair_id'];lid=a['sibling_list_id']
        require(pair_ok(owner,i,family) and positive(lid),'insertion owner/list IDs')
        same(a,dict(step='step3a_insert_pair',**base,boundary_pair_id=boundary,insertion_mode=mode,parent_pair_id=owner,sibling_list_id=lid),'insertion event')
        if mode=='singleton_list':
            require(lid not in seen_ids,'singleton reuses an allocated list ID')
            require(owner==boundary,'singleton owner/list')
            seen_ids.add(lid);live[lid]=(owner,1);calculated['sibling_lists_created']+=1
        else:
            require(lid in live and live[lid][0]==owner,'boundary insertion ownership')
            live[lid]=(owner,live[lid][1]+1);calculated['sibling_list_insertions']+=1
            observations.append(dict(iteration=i,kind='boundary_insert',list_id=lid,owner=owner))
        require(set(b)=={'step',*base,'boundary_pair_id','performed','reason','input_list_id','input_size','left_list_id','left_size','right_list_id','right_size','acquired_side'},'split fields')
        sizes=[b[k] for k in ('input_size','left_size','right_size')]
        require(all(type(x) is int and x>=0 for x in sizes),'split size types')
        boundary=selections[1 if increasing else 0];performed=not encloses(boundary,i-1)
        source=b['input_list_id'];left=b['left_list_id'];right=b['right_list_id'];size,ls,rs=sizes
        side=('left' if increasing else 'right') if performed else None
        same(b,dict(step='step3b_split_sibling_list',**base,boundary_pair_id=boundary,performed=performed,
             reason=None if performed else 'boundary pair encloses previous point',input_list_id=source,input_size=size,
             left_list_id=left,left_size=ls,right_list_id=right,right_size=rs,acquired_side=side),'split event flags/order')
        if performed:
            require(positive(source) and source!=lid and source in live and live[source]==(owner,size) and size>0,'split live source/size/owner')
            require(ls+rs==size and (left is None if ls==0 else positive(left))
                    and (right is None if rs==0 else positive(right)),'split output size/ID')
            require(left is None or right is None or left!=right,'split output alias')
            del live[source]
            for output,amount,output_side in ((left,ls,'left'),(right,rs,'right')):
                if output is not None:
                    require(output not in seen_ids,'split output reuses an allocated list ID')
                    seen_ids.add(output)
                    live[output]=(i if output_side==side else owner,amount)
            calculated['sibling_list_splits']+=1;calculated['split_items_transferred']+=ls if side=='left' else rs
            observations.append(dict(iteration=i,kind='split_source',list_id=source,owner=owner))
            splits.append(dict(iteration=i,source_list_id=source,source_owner=owner,finite_owner=owner>0,
                input_size=size,left_size=ls,right_size=rs,smaller_side=min(ls,rs),left_list_id=left,right_list_id=right,
                left_owner=(i if side=='left' else owner) if left else None,
                right_owner=(i if side=='right' else owner) if right else None,acquired_side=side))
            if backend=='ordinary_list':
                for key in ('sibling_scan_checks','split_items_scanned','split_items_copied'):calculated[key]+=size
        else:
            require(sizes==[0,0,0] and source is None and left is None and right is None,'skip sizes/IDs')
        require(set(c)=={'step',*base,'child_pair_id','base_anchor_point_id','output_anchor_point_id','insertion_side','adjusted_for_z1','processed_count'},'output insertion fields')
        child=c['child_pair_id'];require(child is None or positive(child) and pair_ok(child,i,family),'output child')
        anchor=i-1 if child is None else (max if increasing else min)((child-1,child),key=lambda p:values[p-1])
        adjusted=i%2==1 and (values[anchor-1]<values[0]<values[i-1] if increasing else values[i-1]<values[0]<values[anchor-1])
        output_anchor=1 if adjusted else anchor
        same(c,dict(step='step3c_insert_output_point',**base,child_pair_id=child,base_anchor_point_id=anchor,
            output_anchor_point_id=output_anchor,insertion_side='after' if increasing else 'before',adjusted_for_z1=adjusted,processed_count=i),'output insertion event')
        after=sorted(range(1,i+1),key=lambda p:values[p-1]);at=after.index(i)
        require(after[at-1 if increasing else at+1]==output_anchor,'output anchor adjacency')
        calculated['output_insertions']+=1;calculated['z1_output_anchor_adjustments']+=adjusted
    # Tree scan counters count backend work absent from trace; preserve their
    # integer checks but do not pretend to independently reconstruct them.
    keys=set(names)-({'sibling_scan_checks','split_items_scanned'} if backend=='heterogeneous_finger' else set())
    require(all(metrics[k]==calculated[k] for k in keys),'reconstructed metrics')
    for split in splits:
        follow={}
        for side in ('left','right'):
            lid=split[side+'_list_id'];later=[]
            if lid is not None:
                for event in observations:
                    if event['iteration']>split['iteration'] and event['list_id']==lid:
                        later.append(event)
                        if event['kind']=='split_source':break
            follow[side]=later
        split['subsequent_updates_before_next_split']=follow
    return dict(splits=splits,metric_keys_rebuilt=sorted(keys),physical_tree_proof=False)
