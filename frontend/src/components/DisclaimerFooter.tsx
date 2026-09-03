export const DISCLAIMER =
  'For educational/portfolio purposes only. Not a certified medical device and not intended for clinical diagnosis.'

/** Rendered by the app layout so the disclaimer is visible on every screen. */
export function DisclaimerFooter() {
  return (
    <footer className="border-t border-slate-200 bg-slate-50 px-4 py-3 text-center text-xs text-slate-500">
      {DISCLAIMER}
    </footer>
  )
}
