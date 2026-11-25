# AI Content Studio - Model Selection

Version: v0.3

## Selected Primary Model

Qwen2.5:3b

## Alternative Model

Llama3.2:3b

## Benchmark Summary

| Metric | Qwen2.5:3b | Llama3.2:3b |
|---|---:|---:|
| Average generation time | 24.57 sec | 26.13 sec |
| Average tokens/sec | 49.99 | 44.09 |
| Average output words | 786 | 695 |
| Average concept coverage | 92.5% | 89.29% |

## Decision

Qwen2.5:3b is selected as the primary model because it
demonstrated better average generation speed and concept
coverage across the five benchmark topics.

Llama3.2:3b remains available as an alternative model.

## Limitations

- Concept coverage is keyword-based.
- Technical accuracy requires manual verification.
- Longer output does not necessarily mean better quality.
- Human evaluation is required before final production use.

## Future Improvements

- Add factual accuracy evaluation.
- Compare narration quality.
- Evaluate longer scripts.
- Benchmark additional models.
