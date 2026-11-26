def classify_task(task_type: str, messages: list[dict[str,str]]) -> str:
    text=' '.join(m.get('content','') for m in messages).lower()
    if task_type.lower() in {'reasoning','analysis','complex','strategy'} or any(x in text for x in ('analyze deeply','compare alternatives','step by step','raciocina detalhadamente')):
        return 'advanced'
    return 'flash'
