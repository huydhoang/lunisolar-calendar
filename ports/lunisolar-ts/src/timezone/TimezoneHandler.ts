import type { TDateParts } from '../types';

/** Lightweight timezone conversions using Intl.DateTimeFormat. */
export class TimezoneHandler {
  private _tz: string;

  constructor(timezone: string) {
    this._tz = timezone;
  }

  /**
   * Convert a UTC Date into date parts in the configured timezone.
   */
  utcToTimezoneDate(utcDate: Date): TDateParts {
    const fmt = new Intl.DateTimeFormat('en-US', {
      timeZone: this._tz,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });

    const parts = fmt.formatToParts(utcDate);
    const get = (t: Intl.DateTimeFormatPartTypes) => Number(parts.find((p) => p.type === t)?.value);

    return {
      year: get('year'),
      month: get('month'),
      day: get('day'),
      hour: get('hour'),
      minute: get('minute'),
      second: get('second'),
    };
  }

  /**
   * Produce a Date whose UTC components match the wall time in the configured timezone.
   * Useful for calculations that expect a Date object at the local wall time.
   */
  convertToTimezone(utcDate: Date): Date {
    const p = this.utcToTimezoneDate(utcDate);
    return new Date(Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second));
  }
}
