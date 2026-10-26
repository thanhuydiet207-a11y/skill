---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Lệnh `python3 -m omega doctor --project-root /tmp/khong-phai-git` thoát với mã 2 và báo `fatal: not a git repository`. Dưới đây là đoạn code liên quan trong `omega/__main__.py` (giữ nguyên số dòng của file):

```
220    global ROOT, CONFIG
221    from omega.arguments import parser as make_parser,validate
222    parser=make_parser();args=parser.parse_args();validate(args)
223    if args.project_root:
224        target=Path(args.project_root)
225        if not target.is_absolute() or not target.is_dir():raise ValueError('Project root must be an existing absolute directory')
226        ROOT=target.resolve()
227        if Path(git('rev-parse','--show-toplevel')).resolve()!=ROOT:raise ValueError('Project root must equal its Git checkout root')
410    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
411        print(json.dumps({'error':str(exc)}),file=sys.stderr);sys.exit(2)
```

Dựa trên đoạn code này, hãy chỉ rõ dòng nào gây ra lỗi, vì sao thiết kế đó tồn tại, và vì sao thông báo lỗi hiện tại không giúp người dùng biết phải làm gì. Không cần chạy lệnh nào.
