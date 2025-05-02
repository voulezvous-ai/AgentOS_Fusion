// src/components/AdvisorMessage.jsx  
import React from 'react';  
import { motion } from 'framer-motion';  
import ReactMarkdown from 'react-markdown';  
import remarkGfm from 'remark-gfm';  
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';  
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';  
import StructuredDataRenderer from './StructuredDataRenderer';  
import { useTypingEffect } from '../hooks/useTypingEffect'; // Assuming hook is moved

const logger = { info: console.log, error: console.error, warn: console.warn, debug: console.debug };

function AdvisorMessage({ message, onFollowUpClick }) {  
  const isFromUser = message.role === 'user';  
  const isFromAI = message.role === 'assistant';

  // Determine if content is text (for typing effect) or structured data  
  const isTextContent = typeof message.content === 'string';  
  const isStructuredContent = !isTextContent && typeof message.content === 'object' && message.content !== null;

  // Apply typing effect only to AI text messages  
  const { displayedText: aiTypingText, isComplete: isTypingComplete } = useTypingEffect(  
    (isFromAI && isTextContent) ? message.content : '',  
    15 // Adjust typing speed (ms per char)  
  );

  // --- Markdown Components Configuration ---  
  const markdownComponents = {  
    // Customize code block rendering using SyntaxHighlighter  
    code({ node, inline, className, children, ...props }) {  
      const match = /language-(w+)/.exec(className || '');  
      const lang = match ? match[1] : 'text'; // Default to plain text if no language specified  
      return !inline ? (  
        <SyntaxHighlighter  
          style={atomDark} // Choose your theme  
          language={lang}  
          PreTag="div" // Use div instead of pre for better styling control if needed  
          className="text-xs rounded w-full my-2" // Add vertical margin  
          wrapLongLines={true} // Wrap long lines  
          codeTagProps={{ style: { fontFamily: '"Fira Code", monospace' } }} // Optional: Use a specific font for code  
          {...props}  
        >  
          {String(children).replace(/n$/, '')}  
        </SyntaxHighlighter>  
      ) : (  
        // Inline code style handled by prose class in index.css  
        <code className={className} {...props}>  
          {children}  
        </code>  
      );  
    },  
    // Add other component overrides if needed (e.g., links, images)  
    // a: ({node, ...props}) => <a className="text-fusion-blue hover:underline" target="_blank" rel="noopener noreferrer" {...props} />, // Open external links in new tab  
    // table, th, td: Rely on prose styles defined in index.css for consistency  
  };

  // --- Animation Variants ---  
  const messageVariants = {  
    hidden: { opacity: 0, y: 15, scale: 0.98 },  
    visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.3, ease: "easeOut" } }  
  };  
  const followUpVariants = {  
    hidden: { opacity: 0, y: 10 },  
    visible: { opacity: 1, y: 0, transition: { duration: 0.2, delay: 0.1 } } // Slight delay after message appears  
  };

  return (  
    <motion.div  
        layout // Smoothly animate position changes  
        variants={messageVariants}  
        initial="hidden"  
        animate="visible"  
        // Use theme colors  
        className={`flex mb-6 ${isFromUser ? 'justify-end' : 'justify-start'}`}  
     >  
        {/* Message Bubble */}  
        <div className={`p-4 rounded-lg max-w-[85%] shadow-md ${  
            isFromUser ? 'bg-fusion-blue text-white' : 'bg-fusion-dark text-fusion-text-primary' // Theme colors  
        }`}>

            {/* Content Area: Apply prose styles for markdown */}  
            {/* Ensure prose styles do not conflict excessively with other components */}  
            <div className="prose prose-sm prose-invert max-w-none message-content"> {/* Add prose classes */}  
                 {isFromUser && (  
                    // Render user message directly (assuming plain text)  
                    // Use whitespace-pre-wrap to respect newlines  
                    <p className="whitespace-pre-wrap">{message.content}</p>  
                 )}

                 {isFromAI && isTextContent && (  
                     // Render AI text with typing effect using ReactMarkdown  
                     <ReactMarkdown  
                        children={aiTypingText}  
                        remarkPlugins={[remarkGfm]}  
                        components={markdownComponents}  
                    />  
                 )}

                 {isFromAI && isStructuredContent && (  
                    // Render AI structured data directly (no typing effect)  
                    <StructuredDataRenderer data={message.content} />  
                 )}

                 {/* Typing Indicator (only for AI text content while typing) */}  
                 {isFromAI && isTextContent && !isTypingComplete && (  
                      // Use theme color for pulse  
                      <span className="inline-block w-2 h-2 ml-1 bg-fusion-purple-light rounded-full animate-pulse"></span>  
                 )}  
            </div>

             {/* Follow-up Buttons (show when typing is complete OR if content is structured) */}  
             {isFromAI && (isTypingComplete || isStructuredContent) && message.follow_up_actions && message.follow_up_actions.length > 0 && (  
                 <motion.div  
                     variants={followUpVariants}  
                     initial="hidden"  
                     animate="visible"  
                     // Use theme colors for border  
                     className="mt-3 pt-3 border-t border-fusion-medium flex flex-wrap gap-2" // Theme border  
                 >  
                    {message.follow_up_actions.map((action, index) => (  
                         <motion.button  
                             key={index}  
                             onClick={() => onFollowUpClick(action)}  
                             // Use theme colors for button styling  
                             className="px-3 py-1 rounded-full text-xs font-medium bg-fusion-medium hover:bg-fusion-purple text-fusion-text-secondary hover:text-white transition-colors duration-150 focus:outline-none focus:ring-1 focus:ring-fusion-purple-light"  
                             whileHover={{ scale: 1.05 }}  
                             whileTap={{ scale: 0.95 }}  
                         >  
                            {action.label || "Ação"} {/* Provide default label */}  
                         </motion.button>  
                    ))}  
                 </motion.div>  
             )}  
        </div>  
    </motion.div>  
  );  
}

export default AdvisorMessage;  
