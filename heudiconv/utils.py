"""Utility objects and functions"""

import os
import os.path as op
from tempfile import mkdtemp
from glob import glob
import json
import re
import sys
import shutil
from collections import namedtuple
import copy
import logging
import stat

SeqInfo = namedtuple(
    'SeqInfo',
    ['total_files_till_now',  # 0
     'example_dcm_file',      # 1
     'series_id',             # 2
     'unspecified1',          # 3
     'unspecified2',          # 4
     'unspecified3',          # 5
     'dim1', 'dim2', 'dim3', 'dim4', # 6, 7, 8, 9
     'TR', 'TE',              # 10, 11
     'protocol_name',         # 12
     'is_motion_corrected',   # 13
     'is_derived',            # 14
     'patient_id',            # 15
     'study_description',     # 16
     'referring_physician_name', # 17
     'series_description',    # 18
     'sequence_name',         # 19
     'image_type',            # 20
     'accession_number',      # 21
     'patient_age',           # 22
     'patient_sex',           # 23
     'date'                   # 24
     ]
)

StudySessionInfo = namedtuple(
    'StudySessionInfo',
    [
        'locator',  # possible prefix identifying the study, e.g.
                    # PI/dataset or just a dataset or empty (default)
                    # Note that ATM there should be no multiple DICOMs with the
                    # same StudyInstanceUID which would collide, i.e point to
                    # the same subject/session. So 'locator' is pretty much an
                    # assignment from StudyInstanceUID into some place within
                    # hierarchy
        'session',  # could be None
        'subject',  # should be some ID defined either in cmdline or deduced
    ]
)


class TempDirs(object):
    """A helper to centralize handling and cleanup of dirs"""

    def __init__(self):
        self.dirs = []
        self.exists = op.exists
        self.lgr = logging.getLogger('tempdirs')

    def __call__(self, prefix=None):
        cctmp = '/scratch/akhanf'
        if os.path.isdir(cctmp):
            tmpdir = mkdtemp(prefix='heudiconvDCM', dir=cctmp)
        else:
            tmpdir = mkdtemp(prefix='heudiconvDCM')

        self.dirs.append(tmpdir)
        return tmpdir

    def __del__(self):
        try:
            self.cleanup()
        except AttributeError:
            pass

    def cleanup(self):
        self.lgr.debug("Removing %d temporary directories", len(self.dirs))
        for t in self.dirs[:]:
            self.lgr.debug("Removing %s", t)
            if self:
                self.rmtree(t)
        self.dirs = []

    def rmtree(self, tmpdir):
        if self.exists(tmpdir):
            shutil.rmtree(tmpdir)
        if tmpdir in self.dirs:
            self.dirs.remove(tmpdir)


def docstring_parameter(*sub):
    """ Borrowed from https://stackoverflow.com/a/10308363/6145776 """
    def dec(obj):
        obj.__doc__ = obj.__doc__.format(*sub)
        return obj
    return dec


def anonymize_sid(sid, anon_sid_cmd):
    from subprocess import check_output
    cmd = [anon_sid_cmd, sid]
    return check_output(cmd).strip()


def create_file_if_missing(filename, content):
    """Create file if missing, so we do not
    override any possibly introduced changes"""
    if op.exists(filename):
        return False
    dirname = op.dirname(filename)
    if not op.exists(dirname):
        os.makedirs(dirname)
    with open(filename, 'w') as f:
        f.write(content)
    return True


def mark_sensitive(ds, path_glob=None):
    """

    Parameters
    ----------
    ds : Dataset to operate on
    path_glob : str, optional
      glob of the paths within dataset to work on
    Returns
    -------
    None
    """
    sens_kwargs = dict(
        init=[('distribution-restrictions', 'sensitive')]
    )
    if path_glob:
        paths = glob(op.join(ds.path, path_glob))
        if not paths:
            return
        sens_kwargs['path'] = paths
    ds.metadata(recursive=True, **sens_kwargs)

def read_config(infile):
    with open(infile, 'rt') as fp:
        info = eval(fp.read())
    return info


def write_config(outfile, info):
    from pprint import PrettyPrinter
    with open(outfile, 'wt') as fp:
        fp.writelines(PrettyPrinter().pformat(info))


def _canonical_dumps(json_obj, **kwargs):
    """ Dump `json_obj` to string, allowing for Python newline bug

    Runs ``json.dumps(json_obj, \*\*kwargs), then removes trailing whitespaces
    added when doing indent in some Python versions. See
    https://bugs.python.org/issue16333. Bug seems to be fixed in 3.4, for now
    fixing manually not only for aestetics but also to guarantee the same
    result across versions of Python.
    """
    out = json.dumps(json_obj, **kwargs)
    if 'indent' in kwargs:
        out = out.replace(' \n', '\n')
    return out


def load_json(filename):
    """Load data from a json file

    Parameters
    ----------
    filename : str
        Filename to load data from.

    Returns
    -------
    data : dict
    """
    with open(filename, 'r') as fp:
        data = json.load(fp)
    return data


def save_json(filename, data, indent=4):
    """Save data to a json file

    Parameters
    ----------
    filename : str
        Filename to save data in.
    data : dict
        Dictionary to save in json file.

    """
    with open(filename, 'w') as fp:
        fp.write(_canonical_dumps(data, sort_keys=True, indent=indent))


def json_dumps_pretty(j, indent=2, sort_keys=True):
    """Given a json structure, pretty print it by colliding numeric arrays
    into a line.

    If resultant structure differs from original -- throws exception
    """
    js = _canonical_dumps(j, indent=indent, sort_keys=sort_keys)
    # trim away \n and spaces between entries of numbers
    js_ = re.sub(
        '[\n ]+("?[-+.0-9e]+"?,?) *\n(?= *"?[-+.0-9e]+"?)', r' \1',
        js, flags=re.MULTILINE)
    # uniform no spaces before ]
    js_ = re.sub(" *\]", "]", js_)
    # uniform spacing before numbers
    js_ = re.sub('  *("?[-+.0-9e]+"?)[ \n]*', r' \1', js_)
    # no spaces after [
    js_ = re.sub('\[ ', '[', js_)
    j_ = json.loads(js_)
    # Removed assert as it does not do any floating point comparison
    #assert(j == j_)
    return js_


def treat_infofile(filename):
    """Tune up generated .json file (slim down, pretty-print for humans).
    """
    with open(filename) as f:
        j = json.load(f)

    j_slim = slim_down_info(j)
    j_pretty = json_dumps_pretty(j_slim, indent=2, sort_keys=True)

    set_readonly(filename, False)
    with open(filename, 'wt') as fp:
        fp.write(j_pretty)
    set_readonly(filename)


def slim_down_info(j):
    """Given an aggregated info structure, removes excessive details

    Such as CSA fields, and SourceImageSequence which on Siemens files could be
    huge and not providing any additional immediately usable information.
    If needed, could be recovered from stored DICOMs
    """
    j = copy.deepcopy(j)  # we will do in-place modification on a copy
    dicts = []
    # poor man programming for now
    if 'const' in j.get('global', {}):
        dicts.append(j['global']['const'])
    if 'samples' in j.get('time', {}):
        dicts.append(j['time']['samples'])
    for d in dicts:
        for k in list(d.keys()):
            if k.startswith('Csa') or k.lower() in {'sourceimagesequence'}:
                del d[k]
    return j


def load_heuristic(heuristic_file):
    """Load heuristic from the file, return the module
    """
    path, fname = op.split(heuristic_file)
    sys.path.append(path)
    mod = __import__(fname.split('.')[0])
    mod.filename = heuristic_file
    return mod


def safe_copyfile(src, dest):
    """Copy file but blow if destination name already exists
    """
    if op.isdir(dest):
        dest = op.join(dest, op.basename(src))
    if op.lexists(dest):
        os.unlink(dest)
    shutil.copyfile(src, dest)


# Globals to check filewriting permissions
ALL_CAN_WRITE = (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
ALL_CAN_READ = (stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
assert ALL_CAN_READ >> 1 == ALL_CAN_WRITE  # Assumption in the code

def set_readonly(path, read_only=True):
    """Make file read only or writeable while preserving "access levels"

    So if file was not readable by others, it should remain not readable by
    others.

    Parameters
    ----------
    path : str
    read_only : bool, optional
        If True (default) - would make it read-only. If False, would make it
        writeable for levels where it is readable

    """

    # get current permissions
    perms = stat.S_IMODE(os.lstat(path).st_mode)
    # set new permissions
    if read_only:
        new_perms = perms & (~ALL_CAN_WRITE)
    else:
        # need to set only for those which had read bit set
        # read bit is <<1 away from write bit
        whocanread = perms & ALL_CAN_READ
        thosecanwrite = whocanread >> 1
        new_perms = perms | thosecanwrite
    # apply and return those target permissions
    os.chmod(path, new_perms)
    return new_perms


def is_readonly(path):
    """Return True if it is a fully read-only file (dereferences the symlink)
    """
    # get current permissions
    perms = stat.S_IMODE(os.lstat(os.path.realpath(path)).st_mode)
    # should be true if anyone is allowed to write
    return not bool(perms & ALL_CAN_WRITE)
