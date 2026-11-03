// Validación de mensajes de commit (rúbrica punto 6: Git Health).
// Formato: Conventional Commits, ver CONTRIBUTING.md.
//   <tipo>(<ámbito>): <descripción en imperativo>
//
//   <cuerpo: qué y por qué>
//
//   Refs: #<issue>   |   Closes #<issue>
module.exports = {
    extends: ["@commitlint/config-conventional"],
    parserPreset: {
        parserOpts: {
            // Reconoce «Refs: #3», «Refs victorgaelpch/ApuntIA#3» y «Closes #3».
            referenceActions: ["close", "closes", "closed", "fix", "fixes", "fixed", "resolve", "resolves", "resolved", "refs", "ref"],
            issuePrefixes: ["#"],
        },
    },
    rules: {
        "type-enum": [2, "always", ["feat", "fix", "docs", "test", "perf", "refactor", "style", "ci", "build", "chore", "revert"]],
        "scope-enum": [2, "always", ["back", "front", "api", "full", "docs", "alcance", "deps", "git", "ci", "tests"]],
        "scope-empty": [1, "never"],
        // Las descripciones en español empiezan en minúscula; se permiten nombres propios dentro.
        "subject-case": [0],
        "header-max-length": [2, "always", 100],
        "body-max-line-length": [1, "always", 100],
        // Vincular cada commit a un issue (aviso: los commits de mantenimiento pueden no tenerlo).
        "references-empty": [1, "never"],
    },
};
