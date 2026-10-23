"""Minimal unified bundles for contract/evolution tests; not native skill evaluation."""
from omega.skills import MODES


def write_skill(root):
    folder=root/'.claude/skills/omega'
    (folder/'references').mkdir(parents=True,exist_ok=True)
    text='---\nname: omega\ndescription: Fixture\ndisable-model-invocation: true\n---\n'
    text+='python3 -m omega doctor\npython3 -m omega map\npython3 -m omega plan\n'
    for name,mode in MODES.items():
        text+=f'[{name}]({mode["reference"]})\n'
        (folder/mode['reference']).write_text('\n'.join('python3 -m omega '+c for c in mode['commands'])+'\n')
    (folder/'SKILL.md').write_text(text)
    return text
