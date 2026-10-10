"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeHighlight from "rehype-highlight";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import "./MarkdownRenderer.css";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className }) => {
  return (
    <div className={`prose prose-lg dark:prose-invert max-w-none ${className || ""}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[
          rehypeHighlight,
          [rehypeKatex, { strict: false, throwOnError: false }],
        ]}
        components={{
          code: ({ children, ...props }) => {
            const code = String(children).replace(/\n$/, "");
            const language = (props as any).className?.replace("language-", "") || "";
            return (
              <pre className="language-js" {...props}>
                <code className={`language-${language}`}>{code}</code>
              </pre>
            );
          },
          table: ({ children, ...props }) => (
            <div className="overflow-x-auto my-4">
              <table className="w-full border-collapse" {...props}>
                {children}
              </table>
            </div>
          ),
          th: (props) => (
            <th
              className="border border-gray-300 dark:border-gray-600 px-4 py-2 font-semibold bg-gray-100 dark:bg-gray-800"
              {...props}
            />
          ),
          td: (props) => (
            <td
              className="border border-gray-300 dark:border-gray-600 px-4 py-2"
              {...props}
            />
          ),
          tr: (props) => <tr {...props} />,
          blockquote: (props) => (
            <blockquote
              className="border-l-4 border-primary pl-4 italic my-4 text-gray-700 dark:text-gray-300"
              {...props}
            />
          ),
          hr: () => <hr className="my-6 border-gray-200 dark:border-gray-700" />,
          a: (props) => (
            <a
              className="text-primary hover:underline font-medium"
              target="_blank"
              rel="noopener noreferrer"
              {...props}
            />
          ),
        }}
      />
    </div>
  );
};

export default MarkdownRenderer;