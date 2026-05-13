-- Reads abbreviations from a semicolon-delimited CSV file specified in
-- thesis.abbreviations.file, sorts them alphabetically, and injects the
-- result as thesis.abbreviations.items for use in the LaTeX template.
function Meta(meta)
  local abbr_meta = meta.thesis and meta.thesis.abbreviations
  if not abbr_meta or not abbr_meta.file then return meta end

  local file_path = pandoc.utils.stringify(abbr_meta.file)
  local f = io.open(file_path, "r")
  if not f then
    io.stderr:write("Warning: abbreviations file not found: " .. file_path .. "\n")
    return meta
  end

  local items = {}
  local first = true
  for line in f:lines() do
    if first then
      first = false
    else
      local abbr, meaning = line:match("^([^;]+);(.+)$")
      if abbr and meaning then
        abbr = abbr:match("^%s*(.-)%s*$")
        meaning = meaning:match("^%s*(.-)%s*$")
        table.insert(items, { abbr = abbr, meaning = meaning })
      end
    end
  end
  f:close()

  table.sort(items, function(a, b) return a.abbr:lower() < b.abbr:lower() end)

  local meta_items = pandoc.List()
  for _, item in ipairs(items) do
    meta_items:insert(pandoc.MetaMap({
      abbr = pandoc.MetaInlines({ pandoc.Str(item.abbr) }),
      meaning = pandoc.MetaInlines({ pandoc.Str(item.meaning) }),
    }))
  end

  meta.thesis.abbreviations.items = meta_items
  return meta
end
