module.exports = function(fileInfo, api) {
  const j = api.jscodeshift;
  const root = j(fileInfo.source);
  const count = root.find(j.CallExpression, {
    callee: { object: { name: 'console' }, property: { name: 'log' } }
  }).length;
  return fileInfo.source; // no changes
};
