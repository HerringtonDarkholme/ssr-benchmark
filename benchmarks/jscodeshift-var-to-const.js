module.exports = function(fileInfo, api) {
  const j = api.jscodeshift;
  const root = j(fileInfo.source);
  root.find(j.VariableDeclaration, { kind: 'var' })
    .forEach(p => { p.node.kind = 'const'; });
  return root.toSource();
};
