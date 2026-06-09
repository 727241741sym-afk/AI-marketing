export function printCurrentReport(target = globalThis.window) {
  if (!target || typeof target.print !== "function") {
    return false;
  }

  target.print();
  return true;
}
