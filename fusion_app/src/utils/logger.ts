const LOG_PREFIX = '[FusionApp]'

export const logger = {
  log: (...args: any[]) => console.log(LOG_PREFIX, ...args),
  warn: (...args: any[]) => console.warn(LOG_PREFIX, ...args),
  error: (...args: any[]) => console.error(LOG_PREFIX, ...args),
  debug: (...args: any[]) => console.debug(LOG_PREFIX, ...args),
  info: (...args: any[]) => console.info(LOG_PREFIX, ...args),
  success: (...args: any[]) => console.log(`%c${LOG_PREFIX}`, 'color: green; font-weight: bold;', ...args)
}