// Pure timeline helpers shared with the regression check. Distances are poetic,
// not an astronomical scale simulation.
export const STAGES = [
  ['more than this garden can hold…', 'So let’s go a little further.'],
  ['more than the entire country…', 'All of Australia. From coast to coast. And still more.'],
  ['more than the entire world…', 'Every ocean, every continent, every corner of Earth.'],
  ['more than the whole solar system…', 'Past the sun and every planet. Our love keeps going.'],
  ['more than the entire Milky Way…', 'Every star in our galaxy. Even that isn’t enough.'],
  ['more than the whole universe…', 'All the galaxies. All the stars. And still, we love you more.'],
]
export const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x))
export const ease = x => { x = clamp(x); return x*x*(3-2*x) }
export const lerp = (a,b,t) => a+(b-a)*t
export function timeline(seconds, reduced = false) {
  const step = reduced ? 1.5 : 6
  const elapsed = clamp(seconds, 0, step*6)
  const stage = Math.min(5, Math.floor(elapsed/step))
  return { stage, local: clamp((elapsed-stage*step)/step), progress: elapsed/(step*6), done: seconds >= step*6 }
}
