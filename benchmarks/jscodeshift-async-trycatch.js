module.exports = function(fileInfo, api) {
  const j = api.jscodeshift;
  const root = j(fileInfo.source);
  root.find(j.FunctionDeclaration, { async: true })
    .filter(p => {
      let hasTryCatch = false;
      j(p).find(j.TryStatement).forEach(() => { hasTryCatch = true; });
      return hasTryCatch;
    });
  return fileInfo.source;
};
