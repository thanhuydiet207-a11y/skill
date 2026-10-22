"""One command grammar shared by CLI and conservative hook policy."""
import argparse

COMMANDS=('doctor','map','plan','audit','benchmark','gates','memory','isolate','rollback-check',
          'candidate','compare','context','memory-read','change-plan','change-check','change-attempt',
          'skill-compatibility-audit','effective-policy-explainer','workflow-handoff-contract',
          'skill-interference-benchmark','project-workflow-adapter','evidence-reconciler',
          'memory-reconciliation','context-sufficiency-check')

class PolicyParser(argparse.ArgumentParser):
    def error(self,message):raise ValueError(message)
    def exit(self,status=0,message=None):raise ValueError('Interactive/help option requires review')


def parser(policy=False):
    p=(PolicyParser if policy else argparse.ArgumentParser)(description='OMEGA engineering workflows')
    p.add_argument('command',choices=COMMANDS)
    p.add_argument('--complexity',choices=['low','medium','high'],default='low')
    for flag in ('conflict','compact','summary','include-existing'):
        p.add_argument('--'+flag,action='store_true')
    for flag in ('title','body','name','worktree','skill','baseline','candidate','record','reason',
                 'project-root','gate-config','input','key'):
        p.add_argument('--'+flag)
    for flag in ('select','allow','acceptance','evidence','skill-root','hook-config'):
        p.add_argument('--'+flag,action='append',default=[])
    p.add_argument('--max-bytes',type=int,default=24000)
    p.add_argument('--adapter',choices=['omega','go','jest','junit'],default='omega')
    return p


def validate(args):
    if args.summary and args.command!='gates':raise ValueError('--summary requires gates')
    if args.candidate and not (args.command=='compare' or args.command=='benchmark' and args.skill):
        raise ValueError('--candidate requires compare or benchmark --skill')
    if args.include_existing and args.command!='change-plan':raise ValueError('--include-existing requires change-plan')
