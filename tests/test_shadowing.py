import pytest

from bigbrother.shadowing import find_shadowing

# Trimmed from tqdm #1477: the reporter's script was named select.py.
TQDM_1477 = '''python select.py /Volumes/a /Volumes/b --list=keys.txt --link
Traceback (most recent call last):
  File "/Users/universe/miniconda3/lib/python3.10/site-packages/tqdm/std.py", line 122, in create_mp_lock
    from multiprocessing import RLock
  File "/Users/universe/miniconda3/lib/python3.10/selectors.py", line 318, in SelectSelector
    _select = select.select
AttributeError: module 'select' has no attribute 'select'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/universe/Documents/grida/figma-archives/figma_archiver/scripts/select.py", line 58, in <module>
    main()
AttributeError: type object 'tqdm' has no attribute '_lock'
'''


def test_tqdm_1477_is_caught_from_the_reporters_own_traceback():
    found = find_shadowing(TQDM_1477, "tqdm")
    assert found.module == "select"
    assert found.path.endswith("/scripts/select.py")
    assert found.quote == "AttributeError: module 'select' has no attribute 'select'"


@pytest.mark.parametrize("text", [
    # A Windows path and the "partially initialized" circular import message.
    'File "C:\\\\Users\\\\me\\\\code\\\\random.py", line 3, in <module>\nAttributeError: partially initialized module \'random\' has no attribute \'choice\'',
    # cannot import name ... from the shadowed module.
    'File "/home/me/proj/json.py", line 1\nImportError: cannot import name \'dumps\' from \'json\' (/home/me/proj/json.py)',
    # A file named like the package itself.
    'File "/home/me/tqdm.py", line 2, in <module>\nAttributeError: module \'tqdm\' has no attribute \'tqdm\'',
])
def test_other_shadowing_shapes_are_caught(text):
    assert find_shadowing(text, "tqdm") is not None


@pytest.mark.parametrize("text", [
    # arrow #1154: the error hints at it, but no file of the reporter's is shown. Not enough.
    "AttributeError: partially initialized module 'arrow' has no attribute 'utcnow' (most likely due to a circular import)",
    # The file is the installed library's own, not the reporter's.
    'File "/usr/lib/python3.10/site-packages/foo/select.py", line 3\nAttributeError: module \'select\' has no attribute \'select\'',
    'File "/usr/local/lib/python3.12/json/__init__.py", line 3\nImportError: cannot import name \'x\' from \'json\'',
    # arrow/arrow.py is the arrow package's own module, not a stand-in.
    'File "/home/me/arrow/arrow/arrow.py", line 9\nAttributeError: module \'arrow\' has no attribute \'get\'',
    # The reporter's file has a module's name, but the error is about something else.
    'File "/home/me/select.py", line 3\nAttributeError: module \'os\' has no attribute \'nope\'',
    # A file named after nothing real.
    'File "/home/me/myscript.py", line 3\nAttributeError: module \'myscript\' has no attribute \'x\'',
    # Interactive sessions have no file.
    'File "<stdin>", line 1, in <module>\nAttributeError: module \'select\' has no attribute \'select\'',
])
def test_not_enough_evidence_means_no_claim(text):
    assert find_shadowing(text, "arrow") is None
