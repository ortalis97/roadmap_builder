import { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface CodeBlockProps {
  language?: string;
  children: string;
}

export function CodeBlock({ language, children }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group my-4">
      {/* Copy button */}
      <button
        onClick={handleCopy}
        className="absolute right-2 top-2 px-2 py-1 text-xs bg-gray-200 hover:bg-gray-300 rounded opacity-0 group-hover:opacity-100 transition-opacity z-10"
        aria-label="Copy code"
      >
        {copied ? 'Copied!' : 'Copy'}
      </button>

      {/* Language badge */}
      {language && (
        <span className="absolute left-2 top-2 px-2 py-0.5 text-xs bg-gray-200 text-gray-600 rounded z-10">
          {language}
        </span>
      )}

      <SyntaxHighlighter
        language={language || 'text'}
        style={oneLight}
        showLineNumbers={true}
        lineNumberStyle={{
          minWidth: '2.5em',
          paddingRight: '1em',
          color: '#9ca3af',
          borderRight: '1px solid #e5e7eb',
          marginRight: '1em',
        }}
        customStyle={{
          margin: 0,
          borderRadius: '0.5rem',
          padding: '2.5rem 1rem 1rem 1rem',
          fontSize: '0.875rem',
          border: '1px solid #e5e7eb',
        }}
        codeTagProps={{
          style: {
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
          },
        }}
      >
        {children.trim()}
      </SyntaxHighlighter>
    </div>
  );
}
