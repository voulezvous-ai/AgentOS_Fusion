// src/components/StructuredDataRenderer.jsx  
import React from 'react';  
import ReactMarkdown from 'react-markdown';  
import remarkGfm from 'remark-gfm'; // For tables  
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';  
// Choose a theme (e.g., atomDark, okaidia, tomorrow) - install if needed? Comes with react-syntax-highlighter  
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

const logger = { debug: console.debug, error: console.error, warn: console.warn };

// --- Markdown Table Generation Helpers ---

const generateMarkdownTableHeader = (keys) => {  
    const header = `| ${keys.map(key => key.replace(/|/g, '|')).join(' | ')} |`; // Escape pipes in headers  
    const separator = `| ${keys.map(() => '---').join(' | ')} |`;  
    return `${header}n${separator}`;  
};

const generateMarkdownTableRow = (item, keys) => {  
    const MAX_CELL_LENGTH = 70; // Adjust max cell length  
    const cells = keys.map(key => {  
        let value = item[key];  
        if (value === null || value === undefined) {  
            value = '*null*';  
        } else if (typeof value === 'object') {  
            value = '`[Object]`'; // Placeholder for nested objects/arrays in table cell  
        } else {  
            value = String(value);  
            value = value.replace(/|/g, '|'); // Escape pipes in cell content  
             // Truncate long values  
             if (value.length > MAX_CELL_LENGTH) {  
                 value = value.substring(0, MAX_CELL_LENGTH) + '...';  
             }  
        }  
        return value;  
    });  
    return `| ${cells.join(' | ')} |`;  
};

// --- Component ---

function StructuredDataRenderer({ data }) {  
    // 1. Array of Objects -> Render as Markdown Table  
    if (Array.isArray(data) && data.length > 0 && data.every(item => typeof item === 'object' && item !== null)) {  
        logger.debug("Rendering structured data as Markdown Table");  
        // Get union of all keys from all objects for robust header generation  
        const allKeys = new Set();  
        data.forEach(item => Object.keys(item).forEach(key => allKeys.add(key)));  
        const keys = Array.from(allKeys);

        if (keys.length === 0) return <pre className="text-xs"><code>[Array of Empty Objects]</code></pre>;

        try {  
            const markdownHeader = generateMarkdownTableHeader(keys);  
            const markdownRows = data.map(item => generateMarkdownTableRow(item, keys)).join('n');  
            const markdownTable = `${markdownHeader}n${markdownRows}`;

            return (  
                // Wrapper for horizontal scroll  
                // Apply prose styles for consistent markdown rendering within the message bubble  
                <div className="overflow-x-auto max-w-full prose prose-sm prose-invert message-content">  
                     <ReactMarkdown  
                        children={markdownTable}  
                        remarkPlugins={[remarkGfm]} // Enable GitHub Flavored Markdown (tables)  
                        // Use CSS in index.css to style the table elements (th, td, etc.) via .prose table selectors  
                        // This keeps styling consistent with other markdown content  
                        components={{  
                             // Override default components if absolutely necessary, otherwise rely on prose styles  
                             // table: ({node, ...props}) => <table className="my-custom-table-class" {...props} />,  
                        }}  
                    />  
                </div>  
            );  
        } catch (error) {  
            logger.error("Error generating Markdown table:", error);  
            // Fallback to JSON if table generation fails  
             return (  
                 <SyntaxHighlighter language="json" style={atomDark} className="text-xs rounded w-full" wrapLongLines={true}>  
                    {JSON.stringify(data, null, 2)}  
                </SyntaxHighlighter>  
            );  
        }  
    }  
    // 2. Simple Object -> Render as Formatted JSON  
    else if (typeof data === 'object' && data !== null && !Array.isArray(data)) {  
        logger.debug("Rendering structured data as Formatted JSON");  
        if (Object.keys(data).length === 0) return <pre className="text-xs"><code>{"{ }"}</code></pre>;  
        try {  
             return (  
                // Use SyntaxHighlighter for objects  
                <SyntaxHighlighter language="json" style={atomDark} className="text-xs rounded w-full" wrapLongLines={true}>  
                    {JSON.stringify(data, null, 2)}  
                </SyntaxHighlighter>  
            );  
        } catch (error) {  
             logger.error("Error rendering object as JSON:", error);  
             return <pre className="text-xs bg-fusion-dark p-2 rounded overflow-x-auto"><code>[Error displaying object data]</code></pre>; // Use theme color  
        }  
    }  
    // 3. Fallback for other types (strings, numbers, etc.) or unrecognized structures -> Render as JSON string  
    else {  
        logger.debug("Rendering structured data as JSON string (fallback)");  
        try {  
             return (  
                 // Also use SyntaxHighlighter for fallback for consistency  
                <SyntaxHighlighter language="json" style={atomDark} className="text-xs rounded w-full" wrapLongLines={true}>  
                    {JSON.stringify(data, null, 2)}  
                </SyntaxHighlighter>  
            );  
        } catch (error) {  
             logger.error("Error stringifying fallback data:", error);  
             return <pre className="text-xs"><code>[Unrenderable Data]</code></pre>;  
        }  
    }  
}

export default StructuredDataRenderer;  
