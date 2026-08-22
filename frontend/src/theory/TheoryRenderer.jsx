import { useLayoutEffect, useMemo, useRef, useState } from "react";
import "./theory.css";
import { buildTheoryTree } from "./theoryTree";

export function TheoryDocument({ document, onBlockClick, selectedBlockId, onPracticeNavigate, onAuthorNoteChange }) {
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
          onAuthorNoteChange={onAuthorNoteChange}
        />
      ))}
    </article>
  );
}

function TheoryBlock({ block, depth, onBlockClick, selectedBlockId, onPracticeNavigate, onAuthorNoteChange }) {
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
  const noteRotation = numericSetting(block.settings, "authorNoteRotation", defaultNoteRotation(notePlacement), -45, 45);
  const noteScale = numericSetting(block.settings, "authorNoteScale", 100, 50, 200);
  const noteX = numericSetting(block.settings, "authorNoteX", 50, 0, 100);
  const noteY = numericSetting(block.settings, "authorNoteY", 50, 0, 100);
  const authorNoteProps = {
    text: authorNote,
    placement: notePlacement,
    color: noteColor,
    rotation: noteRotation,
    scale: noteScale,
    x: noteX,
    y: noteY,
    blockId: block.id,
    onBlockClick,
    onChange: onAuthorNoteChange,
  };

  if (block.type === "section") {
    return (
      <details
        className={`theory-section depth-${Math.min(depth, 3)} ${authorNote ? `has-author-note note-${notePlacement}` : ""} ${String(selectedBlockId) === String(block.id) ? "is-selected" : ""}`}
        data-theory-block-id={block.id}
        onClick={click}
      >
        <summary><span><InlineMarkdown value={block.data?.title || "Подраздел"} /></span><i>+</i></summary>
        <div className="theory-section-content">
          {children.map((child) => (
            <TheoryBlock key={child.id} block={child} depth={depth + 1} onBlockClick={onBlockClick} selectedBlockId={selectedBlockId} onPracticeNavigate={onPracticeNavigate} onAuthorNoteChange={onAuthorNoteChange} />
          ))}
        </div>
        {authorNote && <AuthorNote {...authorNoteProps} />}
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
      if (validTarget && onPracticeNavigate) {
        onPracticeNavigate(taskNumber, exerciseSetId);
      } else if (onBlockClick) {
        onBlockClick(block.id);
      }
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
    <div className={`theory-block theory-block-${block.type} ${authorNote ? `has-author-note note-${notePlacement}` : ""} ${String(selectedBlockId) === String(block.id) ? "is-selected" : ""}`} data-theory-block-id={block.id} onClick={click}>
      <div className="theory-block-main">
        <div className="theory-block-content">{content}</div>
        {authorNote && <AuthorNote {...authorNoteProps} />}
      </div>
      {children.length > 0 && <div className="theory-nested">{children.map((child) => <TheoryBlock key={child.id} block={child} depth={depth + 1} onBlockClick={onBlockClick} selectedBlockId={selectedBlockId} onPracticeNavigate={onPracticeNavigate} onAuthorNoteChange={onAuthorNoteChange} />)}</div>}
    </div>
  );
}

function AuthorNote({ text, placement, color, rotation, scale, x, y, blockId, onBlockClick, onChange }) {
  const draggable = Boolean(onChange);
  const noteRef = useRef(null);
  const [freePosition, setFreePosition] = useState(null);

  useLayoutEffect(() => {
    if (placement !== "free") {
      setFreePosition(null);
      return undefined;
    }

    const note = noteRef.current;
    const anchor = note?.closest(".theory-block-main, .theory-section");
    if (!note || !anchor) return undefined;

    const updatePosition = () => {
      const anchorWidth = anchor.clientWidth;
      const anchorHeight = anchor.clientHeight;
      if (!anchorWidth || !anchorHeight) return;

      const bleed = Math.min(14, anchorWidth * 0.04);
      const left = boundedNoteCenter(anchorWidth, note.offsetWidth, x, bleed);
      const top = boundedNoteCenter(anchorHeight, note.offsetHeight, y, bleed);
      setFreePosition((current) => (
        current?.left === left && current?.top === top ? current : { left, top }
      ));
    };

    updatePosition();
    const observer = new ResizeObserver(updatePosition);
    observer.observe(anchor);
    observer.observe(note);
    return () => observer.disconnect();
  }, [placement, rotation, scale, text, x, y]);

  const setPosition = (clientX, clientY, anchor) => {
    if (!anchor || (!clientX && !clientY)) return;
    const bounds = anchor.getBoundingClientRect();
    if (!bounds.width || !bounds.height) return;
    onChange(blockId, {
      authorNotePlacement: "free",
      authorNoteX: clamp(Math.round(((clientX - bounds.left) / bounds.width) * 1000) / 10, 0, 100),
      authorNoteY: clamp(Math.round(((clientY - bounds.top) / bounds.height) * 1000) / 10, 0, 100),
    });
  };
  const startDrag = (event) => {
    if (!draggable) return;
    event.preventDefault();
    event.stopPropagation();
    onBlockClick?.(blockId);
    const anchor = event.currentTarget.closest(".theory-block-main, .theory-section");
    const noteBounds = event.currentTarget.getBoundingClientRect();
    const grabOffsetX = event.clientX - (noteBounds.left + noteBounds.width / 2);
    const grabOffsetY = event.clientY - (noteBounds.top + noteBounds.height / 2);
    const move = (nextEvent) => {
      nextEvent.preventDefault();
      setPosition(nextEvent.clientX - grabOffsetX, nextEvent.clientY - grabOffsetY, anchor);
    };
    const finish = (nextEvent) => {
      setPosition(nextEvent.clientX - grabOffsetX, nextEvent.clientY - grabOffsetY, anchor);
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", finish);
      window.removeEventListener("pointercancel", finish);
    };
    setPosition(event.clientX - grabOffsetX, event.clientY - grabOffsetY, anchor);
    window.addEventListener("pointermove", move, { passive: false });
    window.addEventListener("pointerup", finish);
    window.addEventListener("pointercancel", finish);
  };
  const style = {
    "--note-x": `${x}%`,
    "--note-y": `${y}%`,
    "--note-left": freePosition ? `${freePosition.left}px` : `${x}%`,
    "--note-top": freePosition ? `${freePosition.top}px` : `${y}%`,
    "--note-rotation": `${rotation}deg`,
    "--note-font-size": `${20 * (scale / 100)}px`,
  };
  return <aside ref={noteRef} className={`author-note author-note-${placement} author-note-tone-${color} ${draggable ? "is-draggable" : ""}`} style={style} aria-label="Комментарий автора" onPointerDown={startDrag} onClick={(event) => draggable && event.stopPropagation()}><span><InlineMarkdown value={text} /></span></aside>;
}

function boundedNoteCenter(containerSize, noteSize, percentage, bleed) {
  const desired = containerSize * (percentage / 100);
  const minimum = (noteSize / 2) - bleed;
  const maximum = containerSize - (noteSize / 2) + bleed;
  return minimum > maximum ? containerSize / 2 : clamp(desired, minimum, maximum);
}

function numericSetting(settings, key, fallback, min, max) {
  const value = Number(settings?.[key]);
  return Number.isFinite(value) && settings?.[key] !== "" && settings?.[key] != null
    ? clamp(value, min, max)
    : fallback;
}

function defaultNoteRotation(placement) {
  if (["right-tilted", "top-right", "below-left"].includes(placement)) return 6;
  if (["left-tilted", "top-left", "below-right"].includes(placement)) return -6;
  return 0;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
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
