"""Shared conservative path policy. Not an OS sandbox or full secret scanner."""
from pathlib import Path
import os

PRIVATE_PARTS={'.git','.omega','.aws','.ssh'}
PRIVATE_NAMES={'.env','id_rsa','id_ed25519','credentials','credentials.json'}


def source_files(root,folder,suffixes):
    """Known engine source trees, pruning generated dependencies and refusing symlinks."""
    root=Path(root).resolve();base=root/folder
    if not base.exists() and not base.is_symlink():return []
    source_path(root,str(base))
    pending=[base];files=[];visited=0
    while pending:
        directory=pending.pop();visited+=1
        if visited>1024:raise ValueError('Engine source directory budget exceeded')
        with os.scandir(directory) as entries:
            for entry in entries:
                path=Path(entry.path);relative=path.relative_to(root)
                if entry.name=='__pycache__' or str(relative)=='integration/typescript/node_modules':continue
                if entry.is_symlink():raise ValueError('Symlink engine source refused')
                if entry.is_dir(follow_symlinks=False):pending.append(path)
                elif entry.is_file(follow_symlinks=False) and path.suffix in suffixes:
                    files.append(source_path(root,str(path)))
                    if len(files)>4096:raise ValueError('Engine source file budget exceeded')
    return sorted(files)


def source_path(root, name):
    root=Path(root).resolve()
    candidate=root/name
    if not candidate.is_relative_to(root):raise ValueError('Source escapes repository')
    current=root
    for part in candidate.relative_to(root).parts:
        current=current/part
        if current.is_symlink():raise ValueError('Symlink source refused')
    resolved=candidate.resolve()
    # Check BOTH lexical and resolved names: a private-name symlink must not hide its name.
    for path in (candidate.absolute(),resolved):
        if not path.is_relative_to(root) or path==root:raise ValueError('Source escapes repository')
        rel=path.relative_to(root)
        if any(x in PRIVATE_PARTS for x in rel.parts) or any(x in PRIVATE_NAMES or x.startswith('.env.') for x in rel.parts):
            raise ValueError('Private/runtime sources excluded')
    return resolved


def artifact_path(root, name, kind, must_exist=True):
    root=Path(root).resolve()
    lexical=root/name
    base=root/'.omega'/kind
    # Runtime state must not alias another checkout or policy file, even within root.
    if not lexical.is_relative_to(base) or lexical==base:raise ValueError('Artifact outside expected namespace')
    relative=lexical.relative_to(root)
    current=root
    for part in relative.parts:
        if part in ('.','..'):raise ValueError('Artifact traversal refused')
        current=current/part
        if current.is_symlink():raise ValueError('Symlink artifact refused')
    resolved=lexical.resolve()
    if not resolved.is_relative_to(base.resolve()) or not resolved.is_relative_to(root):raise ValueError('Artifact escapes repository')
    if must_exist and (not resolved.is_file() or resolved.stat().st_size>1048576):raise ValueError('Missing or oversized artifact')
    return resolved
