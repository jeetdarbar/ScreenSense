import codecs
path = r'd:\RM_Python\sleep_app\app\templates\dashboard.html'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

# Replace header box (has slightly different attributes, actually wait, let's just trace exact substrings)

# The base card
text = text.replace(
    'bg-zinc-800/30 backdrop-blur-xl p-6 rounded-2xl shadow-2xl border border-zinc-700/50',
    'bg-gradient-to-br from-zinc-800/40 to-zinc-900/10 backdrop-blur-2xl p-8 rounded-3xl border border-zinc-700/50 border-t-zinc-600/50 shadow-2xl shadow-zinc-950/50'
)

text = text.replace(
    'bg-zinc-800/30 backdrop-blur-xl p-6 rounded-2xl border border-zinc-700/50 flex flex-col md:flex-row items-center justify-between shadow-2xl',
    'bg-gradient-to-br from-zinc-800/40 to-zinc-900/10 backdrop-blur-2xl p-8 rounded-3xl border border-zinc-700/50 border-t-zinc-600/50 shadow-2xl shadow-zinc-950/50 flex flex-col md:flex-row items-center justify-between'
)

text = text.replace(
    'bg-zinc-800/30 backdrop-blur-xl p-6 rounded-2xl border border-zinc-700/50 shadow-2xl',
    'bg-gradient-to-br from-zinc-800/40 to-zinc-900/10 backdrop-blur-2xl p-8 rounded-3xl border border-zinc-700/50 border-t-zinc-600/50 shadow-2xl shadow-zinc-950/50'
)

text = text.replace(
    'bg-zinc-800/30 backdrop-blur-xl rounded-2xl border border-amber-500/20 shadow-[0_0_15px_rgba(251,191,36,0.05)]',
    'bg-gradient-to-br from-zinc-800/40 to-zinc-900/10 backdrop-blur-2xl rounded-3xl border border-amber-500/30 border-t-amber-400/30 shadow-[0_0_30px_rgba(251,191,36,0.1)]'
)

text = text.replace(
    'bg-zinc-800/30 backdrop-blur-xl p-8 rounded-2xl border border-zinc-700/50 shadow-2xl',
    'bg-gradient-to-br from-zinc-800/40 to-zinc-900/10 backdrop-blur-2xl p-8 rounded-3xl border border-zinc-700/50 border-t-zinc-600/50 shadow-2xl shadow-zinc-950/50'
)

text = text.replace(
    'bg-zinc-950/80 backdrop-blur-2xl transition-opacity',
    'bg-zinc-950/90 backdrop-blur-[32px] transition-opacity'
)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(text)
