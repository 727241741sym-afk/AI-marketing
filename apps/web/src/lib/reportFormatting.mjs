function normalizeReportText(value) {
  return String(value ?? "")
    .replace(/\r\n?/g, "\n")
    .replace(/\u00a0/g, " ")
    .replace(/[ \t]+---[ \t]+/g, "\n---\n")
    .replace(/[ \t]+(#{2,6})[ \t]+/g, "\n$1 ")
    .replace(/^([A-Za-z][A-Za-z\s]+:\s+)(#{1,6})[ \t]+/gm, "$1\n$2 ")
    .trim();
}

function createParagraphBlock(lines) {
  const text = lines.join(" ").replace(/\s+/g, " ").trim();
  return text ? { type: "paragraph", text } : null;
}

function flushParagraph(blocks, paragraphLines) {
  const block = createParagraphBlock(paragraphLines);
  if (block) {
    blocks.push(block);
  }
  paragraphLines.length = 0;
}

function parseListItem(line) {
  const unordered = line.match(/^[-*]\s+(.+)$/);
  if (unordered) {
    return { ordered: false, text: unordered[1].trim() };
  }

  const ordered = line.match(/^\d+[.)]\s+(.+)$/);
  if (ordered) {
    return { ordered: true, text: ordered[1].trim() };
  }

  return null;
}

export function parseReportContent(value) {
  const lines = normalizeReportText(value)
    .split("\n")
    .map((line) => line.trim());
  const blocks = [];
  const paragraphLines = [];
  let listBlock = null;

  function flushList() {
    if (listBlock?.items.length) {
      blocks.push(listBlock);
    }
    listBlock = null;
  }

  for (const line of lines) {
    if (!line) {
      flushParagraph(blocks, paragraphLines);
      flushList();
      continue;
    }

    if (/^(-{3,}|\*{3,}|_{3,})$/.test(line)) {
      flushParagraph(blocks, paragraphLines);
      flushList();
      blocks.push({ type: "rule" });
      continue;
    }

    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      flushParagraph(blocks, paragraphLines);
      flushList();
      blocks.push({
        type: "heading",
        depth: heading[1].length,
        text: heading[2].replace(/\s+/g, " ").trim(),
      });
      continue;
    }

    const listItem = parseListItem(line);
    if (listItem) {
      flushParagraph(blocks, paragraphLines);
      if (!listBlock || listBlock.ordered !== listItem.ordered) {
        flushList();
        listBlock = { type: "list", ordered: listItem.ordered, items: [] };
      }
      listBlock.items.push(listItem.text);
      continue;
    }

    flushList();
    paragraphLines.push(line);
  }

  flushParagraph(blocks, paragraphLines);
  flushList();

  return blocks.length ? blocks : [{ type: "paragraph", text: "此區塊尚無內容。" }];
}

export function parseInlineFormatting(value) {
  const text = String(value ?? "");
  const tokens = [];
  const pattern = /(\*\*([^*]+)\*\*|`([^`]+)`)/g;
  let index = 0;
  let match;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > index) {
      tokens.push({ type: "text", text: text.slice(index, match.index) });
    }
    tokens.push({
      type: match[2] ? "strong" : "code",
      text: match[2] ?? match[3] ?? "",
    });
    index = pattern.lastIndex;
  }

  if (index < text.length) {
    tokens.push({ type: "text", text: text.slice(index) });
  }

  return tokens.filter((token) => token.text);
}
