import re

html_path = r'd:\RM_Python\sleep_app\app\templates\dashboard.html'
js_path = r'd:\RM_Python\sleep_app\app\static\js\app.js'

with open(html_path, 'r', encoding='utf-8') as f:
    h = f.read()

# 1. Premium Glass Cards
glass_find = 'bg-white/5 backdrop-blur-lg p-6 rounded-2xl border border-white/10 shadow-xl'
glass_replace = 'bg-gradient-to-br from-zinc-800/40 to-zinc-900/10 backdrop-blur-2xl p-8 rounded-3xl shadow-2xl shadow-zinc-950/50 border border-zinc-700/50 border-t-zinc-600/50'
h = h.replace(glass_find, glass_replace)

h = h.replace('bg-white p-8 md:p-12', 'bg-gradient-to-br from-zinc-800/40 to-zinc-900/10 backdrop-blur-2xl p-8 md:p-12 border border-zinc-700/50 border-t-zinc-600/50 shadow-2xl shadow-zinc-950/50 rounded-3xl')
h = h.replace('bg-white w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-3xl shadow-2xl relative', 'bg-zinc-900 w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-3xl shadow-2xl relative border border-zinc-700/50')

# 2. Typography Colors
h = h.replace('text-white', 'text-stone-200')
h = h.replace('text-gray-800', 'text-stone-200')
h = h.replace('text-gray-900', 'text-stone-200')
h = h.replace('text-gray-600', 'text-stone-400')
h = h.replace('text-gray-500', 'text-stone-400')
h = h.replace('text-gray-400', 'text-stone-400')
h = h.replace('text-gray-300', 'text-stone-300')
h = h.replace('text-slate-800', 'text-stone-200')
h = h.replace('text-slate-400', 'text-stone-400')
h = h.replace('text-indigo-600', 'text-amber-500')
h = h.replace('text-indigo-500', 'text-amber-500')
h = h.replace('text-indigo-400', 'text-amber-500')
h = h.replace('text-indigo-300', 'text-amber-400')
h = h.replace('text-indigo-200', 'text-amber-200')
h = h.replace('text-indigo-100', 'text-amber-100')

# 3. Background Colors
h = h.replace('bg-slate-950', 'bg-zinc-950')
h = h.replace('bg-slate-900', 'bg-zinc-900')
h = h.replace('bg-slate-800', 'bg-zinc-800')
h = h.replace('bg-slate-50', 'bg-zinc-900')
h = h.replace('bg-indigo-600', 'bg-amber-600')
h = h.replace('bg-indigo-500', 'bg-amber-500')
h = h.replace('bg-indigo-900', 'bg-zinc-900')
h = h.replace('bg-indigo-950', 'bg-zinc-950')
h = h.replace('bg-gray-50', 'bg-zinc-900/50')
h = h.replace('bg-gray-100', 'bg-zinc-800')

# 4. Borders
h = h.replace('border-slate-800', 'border-zinc-800')
h = h.replace('border-indigo-500', 'border-amber-500')
h = h.replace('border-indigo-400', 'border-amber-400')
h = h.replace('border-gray-200', 'border-zinc-700/50')
h = h.replace('border-gray-100', 'border-zinc-800/50')

# 5. Focus Rings and Inputs
h = h.replace('focus:ring-indigo-500', 'focus:ring-1 focus:ring-amber-500/50')
h = h.replace('focus:border-indigo-500', 'focus:border-amber-500/50 outline-none')
# Convert light mode inputs to dark amber inputs
h = re.sub(r'class="w-full px-4 py-3 rounded-xl border border-gray-200 (.*?)"', r'class="w-full px-4 py-3 rounded-xl bg-zinc-950/50 border border-zinc-800 focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/50 outline-none text-amber-50 \1"', h)

# 6. Wind-Down specific
h = h.replace('rgba(99, 102, 241', 'rgba(251, 191, 36') # breathing shadow animation
h = h.replace('backdrop-blur-xl transition-opacity', 'backdrop-blur-[32px] transition-opacity')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(h)

# Now apply similar color shifts to app.js
with open(js_path, 'r', encoding='utf-8') as f:
    j = f.read()

j = j.replace('text-gray-800', 'text-stone-200')
j = j.replace('text-gray-600', 'text-stone-400')
j = j.replace('text-gray-500', 'text-stone-400')
j = j.replace('text-indigo-600', 'text-amber-500')
j = j.replace('text-indigo-500', 'text-amber-500')
j = j.replace('text-indigo-400', 'text-amber-500')
j = j.replace('text-indigo-300', 'text-amber-400')
j = j.replace('bg-white', 'bg-zinc-900/40')
j = j.replace('border-gray-100', 'border-zinc-800')
j = j.replace('rgba(99, 102, 241,', 'rgba(251, 191, 36,') # Indigo to amber in charts

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(j)

print("Theme applied successfully to original layout.")
