---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Đoạn code sau trong `omega/__main__.py` gây ra thông báo `fatal: not a git repository` khi `--project-root` không phải Git repo:

```
223    if args.project_root:
224        target=Path(args.project_root)
225        if not target.is_absolute() or not target.is_dir():raise ValueError('Project root must be an existing absolute directory')
226        ROOT=target.resolve()
227        if Path(git('rev-parse','--show-toplevel')).resolve()!=ROOT:raise ValueError('Project root must equal its Git checkout root')
410    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
411        print(json.dumps({'error':str(exc)}),file=sys.stderr);sys.exit(2)
```

Lập kế hoạch (chưa sửa code) để báo lỗi rõ hơn trong trường hợp này. Nêu file và dòng cần sửa, acceptance kiểm chứng được bằng lệnh hoặc test cụ thể, cách rollback, và giữ phạm vi nhỏ nhất.
