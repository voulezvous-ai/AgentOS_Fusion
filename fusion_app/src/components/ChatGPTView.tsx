// Dentro do componente GptMessageBubble
const bgColor = turn.role === 'user' ? 'bg-sky-900/70'
              : turn.role === 'assistant' ? 'bg-gray-800/80'
              : turn.role === 'error' ? 'bg-red-900/60 text-red-200'
              : 'bg-gray-900/50 text-gray-400 italic'; // 'system'

const isIntermediate = turn.type === 'intermediate_step';
return (
  <div className={... + (isIntermediate ? ' opacity-70' : '')}>
    <div className={... + (isIntermediate ? ' prose-p:italic' : '')}>
      <ReactMarkdown>{turn.text || ''}</ReactMarkdown>
    </div>
  </div>
);
