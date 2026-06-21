const TOKEN_SPLIT_RE = /[\s,;:/\\|._()[\]{}"'`~!@#$%^&*+=<>?]+|[-–—]+/g;

const MEDICAL_ALIAS_GROUPS = [
  ["hen", "hen phế quản", "suyễn", "asthma"],
  ["tieu duong", "đái tháo đường", "diabetes", "type 2 diabetes"],
  ["dai thao duong", "tiểu đường", "diabetes"],
  ["cao huyet ap", "tăng huyết áp", "hypertension"],
  ["tang huyet ap", "cao huyết áp", "hypertension"],
  ["dau dau", "headache", "migraine"],
  ["di ung", "allergy", "allergic"],
  ["nhiem khuan", "infection", "bacterial infection", "nhiễm trùng"],
  ["viem mui", "rhinitis"],
  ["viem hong", "pharyngitis", "sore throat"],
  ["viem phe quan", "bronchitis"],
  ["trao nguoc", "reflux", "gerd"],
];

function unique(values) {
  return Array.from(new Set(values.filter(Boolean)));
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function hasTokenPhrase(text, phrase) {
  if (!phrase) return false;
  return new RegExp(`(^|\\s)${escapeRegExp(phrase)}($|\\s)`).test(text);
}

export function removeVietnameseTones(value) {
  return String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[đĐ]/g, "d");
}

export function normalizeText(value) {
  return removeVietnameseTones(value)
    .toLowerCase()
    .replace(TOKEN_SPLIT_RE, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function tokenizeText(value) {
  const normalized = normalizeText(value);
  return normalized ? normalized.split(" ").filter(Boolean) : [];
}

export function expandMedicalAliases(keyword) {
  const normalizedKeyword = normalizeText(keyword);
  if (!normalizedKeyword) {
    return { terms: [], aliasUsed: false };
  }

  const terms = [normalizedKeyword];
  MEDICAL_ALIAS_GROUPS.forEach((group) => {
    const normalizedGroup = group.map(normalizeText);
    const matchesGroup = normalizedGroup.some(
      (alias) => normalizedKeyword === alias || hasTokenPhrase(normalizedKeyword, alias),
    );

    if (matchesGroup) {
      terms.push(...normalizedGroup);
    }
  });

  const expanded = unique(terms);
  return {
    terms: expanded,
    aliasUsed: expanded.length > 1,
  };
}

function normalizeFields(item, fieldGetter) {
  return fieldGetter(item)
    .map((field) => {
      const rawField = typeof field === "string" ? { value: field } : field;
      const normalized = normalizeText(rawField?.value);
      return {
        text: normalized,
        tokens: new Set(tokenizeText(rawField?.value)),
        weight: Number(rawField?.weight || 1),
      };
    })
    .filter((field) => field.text);
}

function scoreTermAgainstField(term, field) {
  const termTokens = tokenizeText(term);
  if (!termTokens.length) return 0;

  let score = 0;

  if (field.text === term) {
    score += 140;
  }

  if (hasTokenPhrase(field.text, term)) {
    score += termTokens.length > 1 ? 110 : 95;
  }

  const wholeTokenMatches = termTokens.filter((token) => field.tokens.has(token));
  if (wholeTokenMatches.length === termTokens.length) {
    score += 70 + termTokens.length * 8;
  } else {
    score += wholeTokenMatches.length * 24;
  }

  termTokens.forEach((token) => {
    if (field.tokens.has(token) || token.length < 4) return;
    const fieldTokens = Array.from(field.tokens);
    if (fieldTokens.some((fieldToken) => fieldToken.startsWith(token))) {
      score += 26;
    } else if (fieldTokens.some((fieldToken) => fieldToken.length >= 5 && fieldToken.includes(token))) {
      score += 10;
    }
  });

  return score * field.weight;
}

export function getSearchScore(item, keyword, fieldGetter) {
  const { terms, aliasUsed } = expandMedicalAliases(keyword);
  if (!terms.length) return { score: 0, aliasUsed };

  const fields = normalizeFields(item, fieldGetter);
  if (!fields.length) return { score: 0, aliasUsed };

  let bestScore = 0;
  terms.forEach((term, termIndex) => {
    const termScore = fields.reduce(
      (sum, field) => sum + scoreTermAgainstField(term, field),
      0,
    );
    const aliasPenalty = termIndex === 0 ? 1 : 0.86;
    bestScore = Math.max(bestScore, termScore * aliasPenalty);
  });

  return { score: bestScore, aliasUsed };
}

export function filterAndRankCatalog(items, keyword, fieldGetter) {
  const { aliasUsed } = expandMedicalAliases(keyword);
  const ranked = items
    .map((item) => {
      const { score } = getSearchScore(item, keyword, fieldGetter);
      return { item, score };
    })
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score)
    .map((entry) => entry.item);

  return { items: ranked, total: ranked.length, aliasUsed };
}
