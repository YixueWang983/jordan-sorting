"""Author entry point: common then targeted, with no analysis between campaigns."""
import argparse
from pathlib import Path
from matched_measurement import run
from qualify_common_inputs import read


def execute(output, qualification, calibration, review_path):
    review=read(review_path)  # Must already exist, completed by the author.
    if output.exists():raise FileExistsError('use a new output directory; no retries or replacement')
    for dataset in ('common','targeted_split'):
        if not run(output/dataset,'formal',dataset,qualification/dataset,
                   calibration=calibration/dataset,review=review,configuration='uninstrumented'):
            return False
    return True


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('output','qualification','calibration','review'):
        p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    raise SystemExit(0 if execute(a.output,a.qualification,a.calibration,a.review) else 2)
