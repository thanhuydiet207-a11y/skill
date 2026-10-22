"""Shared conservative path policy. Not an OS sandbox or full secret scanner."""
from pathlib import Path

PRIVATE_PARTS={'.git','.omega','.aws','.ssh'}
PRIVATE_NAMES={'.env','id_rsa','id_ed25519','credentials','credentials.json'}


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
