import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import { CodeBlock } from './CodeBlock';

interface MarkdownContentProps {
  content: string;
  className?: string;
  direction?: 'ltr' | 'rtl';
}

export function MarkdownContent({
  content,
  className = '',
  direction = 'ltr',
}: MarkdownContentProps) {
  return (
    <div
      dir={direction}
      className={`prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gray-900 prose-ul:text-gray-700 prose-ol:text-gray-700 prose-code:text-gray-800 prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded ${className}`}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            const codeString = String(children).replace(/\n$/, '');

            // Fenced code block (has language or multiline) - always LTR
            if (match || codeString.includes('\n')) {
              return (
                <div dir="ltr">
                  <CodeBlock language={match?.[1]}>{codeString}</CodeBlock>
                </div>
              );
            }

            // Inline code
            return (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
          // Style details/summary for expandable hints
          details({ children, ...props }) {
            return (
              <details
                className="my-4 border border-gray-200 rounded-lg overflow-hidden"
                {...props}
              >
                {children}
              </details>
            );
          },
          summary({ children, ...props }) {
            return (
              <summary
                className="px-4 py-3 bg-gray-50 cursor-pointer hover:bg-gray-100 font-medium text-gray-700"
                {...props}
              >
                {children}
              </summary>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
