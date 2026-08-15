import { useMemo } from "react";
import "./theory.css";

export function buildTheoryTree(blocks = []) {
  if (blocks.some((block) => Array.isArray(block.children))) return blocks;
  const children = new Map();
  const ids = new Set(blocks.map((block) => block.id));
  blocks.forEach((block) => {
    const parent = block.parentId != null && ids.has(block.parentId) ? block.parentId : null;
    children.set(parent, [...(children.get(parent) || []), block]);
  });
  children.forEach((items) => items.sort(
    (left, right) => (left.sortOrder ?? 0) - (right.sortOrder ?? 0)
      || String(left.id).localeCompare(String(right.id)),
  ));
  const attach = (block, ancestors = new Set()) => {
    if (ancestors.has(block.id)) return { ...block, children: [] };
    const next = new Set(ancestors).add(block.id);
    return { ...block, children: (children.get(block.id) || []).map((item) => attach(item, next)) };
  };
  return (children.get(null) || []).map((block) => attach(block));
}

export function TheoryDocument({ document, onBlockClick, selectedBlockId, onPracticeNavigate }) {
  const tree = useMemo(() => buildTheoryTree(document?.blocks || []), [document]);
  return (
    <article className="theory-document">
      {tree.map((block) => (
        <TheoryBlock
          key={block.id}
          block={block}
          depth={0}
          onBlockClick={onBlockClick}
          selectedBlockId={selectedBlockId}
          onPracticeNavigate={onPracticeNavigate}
        />
      ))}
    </article>
  );
}

function TheoryBlock({ block, depth, onBlockClick, selectedBlockId, onPracticeNavigate }) {
  const children = block.children || [];
  const markdown = block.data?.markdown || "";
  const click = (event) => {
    if (!onBlockClick) return;
    event.stopPropagation();
    onBlockClick(block.id);
  };
  const authorNote = String(block.settings?.authorNote || "").trim();
  const requestedPlacement = block.settings?.authorNotePlacement || "auto";
  const legacyPlacement = { angled: "right-tilted", vertical: "vertical-right", below: "below-right" }[requestedPlacement] || requestedPlacement;
  const notePlacement = legacyPlacement === "auto"
    ? block.type === "table" ? "vertical-right" : ["callout", "example"].includes(block.type) ? "right-tilted" : "below-right"
    : legacyPlacement;
  const noteColor = block.settings?.authorNoteColor || "note";

  if (block.type === "section") {
    return (
      <details
        className={`theory-section depth-${Math.min(depth, 3)} ${authorNote ? `has-author-note note-${notePlacement}` : ""} ${selectedBlockId === block.id ? "is-selected" : ""}`}
        onClick={click}
      >
        <summary><span><InlineMarkdown value={block.data?.title || "Подраздел"} /></span><i>+</i></summary>
        <div className="theory-section-content">
          {children.map((child) => (
            <TheoryBlock key={child.id} block={child} depth={depth + 1} onBlockClick={onBlockClick} selectedBlockId={selectedBlockId} onPracticeNavigate={onPracticeNavigate} />
          ))}
        </div>
        {authorNote && <AuthorNote text={authorNote} placement={notePlacement} color={noteColor} />}
      </details>
    );
  }

  let content;
  if (block.type === "callout") {
    content = <fieldset className={`callout callout-${block.data?.variant || "note"}`}><legend>{calloutLabel(block.data?.variant)}</legend><Markdown value={markdown} /></fieldset>;
  } else if (block.type === "example") {
    content = <fieldset className="example-block"><legend>Пример</legend><Markdown value={markdown} /></fieldset>;
  } else if (block.type === "image") {
    const source = block.data?.sourceType === "inline_svg"
      ? `data:image/svg+xml;charset=utf-8,${encodeURIComponent(block.data?.svg || "")}`
      : block.data?.url;
    content = source ? <figure className="theory-image"><img src={source} alt={block.data?.alt || ""} />{block.data?.caption && <figcaption><InlineMarkdown value={block.data.caption} /></figcaption>}</figure> : null;
  } else if (block.type === "list") {
    const Tag = block.data?.style === "ordered" ? "ol" : "ul";
    content = <Tag className="theory-list">{(block.data?.items || []).map((item, index) => <li key={index}><InlineMarkdown value={String(item?.text || item)} /></li>)}</Tag>;
  } else if (block.type === "table") {
    content = <div className="table-scroll"><table><tbody>{(block.data?.rows || []).map((row, rowIndex) => <tr key={rowIndex}>{(row?.cells || row || []).map((cell, cellIndex) => <td key={cellIndex}><InlineMarkdown value={String(cell?.text || cell || "")} /></td>)}</tr>)}</tbody></table></div>;
  } else if (block.type === "video_embed" && block.data?.url) {
    content = <a className="video-link" href={safeUrl(block.data.url) || "#"} target="_blank" rel="noreferrer">Открыть видео <span>↗</span></a>;
  } else if (block.type === "practice_link") {
    const taskNumber = Number(block.data?.taskNumber);
    const exerciseSetId = Number(block.data?.exerciseSetId) || null;
    const validTarget = Number.isInteger(taskNumber) && taskNumber > 0;
    const followLink = (event) => {
      event.stopPropagation();
      if (validTarget && onPracticeNavigate) onPracticeNavigate(taskNumber, exerciseSetId);
    };
    content = (
      <aside className="practice-link-card">
        <span className="practice-link-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24"><path d="M7 3.5h10v17L12 17l-5 3.5v-17Z" /></svg>
        </span>
        <div className="practice-link-copy"><Markdown value={markdown} /></div>
        <button type="button" onClick={followLink} aria-disabled={!validTarget || !onPracticeNavigate}>
          {block.data?.buttonLabel || "Перейти к тренажёру"}<span aria-hidden="true">→</span>
        </button>
      </aside>
    );
  } else {
    const variant = block.settings?.variant;
    if (variant === "heading_1") content = <h2><InlineMarkdown value={markdown} /></h2>;
    else if (variant === "heading_2") content = <h3><InlineMarkdown value={markdown} /></h3>;
    else content = <Markdown value={markdown} />;
  }

  return (
    <div className={`theory-block theory-block-${block.type} ${authorNote ? `has-author-note note-${notePlacement}` : ""} ${selectedBlockId === block.id ? "is-selected" : ""}`} onClick={click}>
      <div className="theory-block-main">
        <div className="theory-block-content">{content}</div>
        {authorNote && <AuthorNote text={authorNote} placement={notePlacement} color={noteColor} />}
      </div>
      {children.length > 0 && <div className="theory-nested">{children.map((child) => <TheoryBlock key={child.id} block={child} depth={depth + 1} onBlockClick={onBlockClick} selectedBlockId={selectedBlockId} onPracticeNavigate={onPracticeNavigate} />)}</div>}
    </div>
  );
}

function AuthorNote({ text, placement, color }) {
  return <aside className={`author-note author-note-${placement} author-note-tone-${color}`} aria-label="Комментарий автора"><span><InlineMarkdown value={text} /></span></aside>;
}

function calloutLabel(variant) {
  return { warning: "Обратите внимание", rule: "Правило", important: "Важно", tip: "Подсказка", note: "Примечание" }[variant] || "Примечание";
}

export function Markdown({ value }) {
  const lines = String(value || "").replace(/\r/g, "").split("\n");
  const nodes = [];
  let paragraph = [];
  let list = [];
  let ordered = false;
  const flushParagraph = () => {
    if (!paragraph.length) return;
    nodes.push(<p key={`p-${nodes.length}`}><InlineMarkdown value={paragraph.join("\n")} /></p>);
    paragraph = [];
  };
  const flushList = () => {
    if (!list.length) return;
    const Tag = ordered ? "ol" : "ul";
    nodes.push(<Tag key={`l-${nodes.length}`}>{list.map((item, index) => <li key={index}><InlineMarkdown value={item} /></li>)}</Tag>);
    list = [];
  };
  lines.forEach((line) => {
    const listMatch = line.match(/^\s*(?:(\d+)\.|[-*])\s+(.+)$/);
    if (listMatch) {
      flushParagraph();
      const nextOrdered = Boolean(listMatch[1]);
      if (list.length && nextOrdered !== ordered) flushList();
      ordered = nextOrdered;
      list.push(listMatch[2]);
    } else {
      flushList();
      const heading = line.match(/^(#{1,3})\s+(.+)$/);
      if (heading) {
        flushParagraph();
        const Tag = `h${Math.min(heading[1].length + 1, 4)}`;
        nodes.push(<Tag key={`h-${nodes.length}`}><InlineMarkdown value={heading[2]} /></Tag>);
      } else if (/^>\s?/.test(line)) {
        flushParagraph();
        nodes.push(<blockquote key={`q-${nodes.length}`}><InlineMarkdown value={line.replace(/^>\s?/, "")} /></blockquote>);
      } else if (!line.trim()) {
        flushParagraph();
      } else {
        paragraph.push(line);
      }
    }
  });
  flushList();
  flushParagraph();
  return <div className="rich-text">{nodes}</div>;
}

export function InlineMarkdown({ value }) {
  const parts = String(value || "").split(/(\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|~~[^~]+~~|`[^`]+`|\*[^*\n]+\*)/g);
  return parts.filter(Boolean).map((part, index) => {
    const link = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (link) {
      const href = safeUrl(link[2]);
      return href ? <a key={index} href={href} target={href.startsWith("/") ? undefined : "_blank"} rel="noreferrer">{link[1]}</a> : link[1];
    }
    if (part.startsWith("**")) return <strong key={index}>{part.slice(2, -2)}</strong>;
    if (part.startsWith("~~")) return <del key={index}>{part.slice(2, -2)}</del>;
    if (part.startsWith("`")) return <code key={index}>{part.slice(1, -1)}</code>;
    if (part.startsWith("*")) return <em key={index}>{part.slice(1, -1)}</em>;
    return part.split("\n").map((line, lineIndex) => <span key={`${index}-${lineIndex}`}>{line}{lineIndex < part.split("\n").length - 1 && <br />}</span>);
  });
}

function safeUrl(value) {
  const url = String(value || "").trim();
  return /^(https?:\/\/|mailto:|tg:\/\/|\/)/i.test(url) ? url : "";
}
