package helpers

import (
	"time"
)

const (
	DEFAULT_DATE_FORMAT = "2006-01-02"
	DEFAULT_TIME_FORMAT = "2006-01-02 15:04:05"
)

func ParseStringToDateDefault(value string) *time.Time {
	return ParseStringToTime(DEFAULT_DATE_FORMAT, value)
}

func ParseStringToTime(layout string, value string) *time.Time {
	t, err := time.Parse(layout, value)
	if err != nil {
		return nil
	}
	return &t
}

func ParseTimeToStringDateDefault(value *time.Time) string {
	return ParseTimeToString(DEFAULT_DATE_FORMAT, value)
}

func ParseTimeToString(layout string, value *time.Time) string {
	if value == nil {
		return ""
	}
	return value.Format(layout)
}

func NewDate(day int, month time.Month, year int) *time.Time {
	t := time.Date(year, month, day, 0, 0, 0, 0, time.Now().Location())
	return &t
}

func NewDateForDayOfWeek(dayOffWeek time.Weekday, month time.Month, year int, number int) *time.Time {
	if number == 0 {
		return nil
	}
	var result *time.Time
	var num int
	for i := 1; i <= 31; i++ {
		t := time.Date(year, month, i, 0, 0, 0, 0, time.Now().Location())
		if t.Month() != month {
			break
		}
		if t.Weekday() == dayOffWeek {
			num++
		}
		if num == number {
			result = &t
			break
		}
	}
	return result
}

func NewLastDateForDayOfWeek(dayOffWeek time.Weekday, month time.Month, year int) *time.Time {
	var result *time.Time
	var num int
	for i := 1; i <= 31; i++ {
		t := time.Date(year, month, i, 0, 0, 0, 0, time.Now().Location())
		if t.Month() != month {
			break
		}
		if t.Weekday() == dayOffWeek {
			num++
		}
		if num == num {
			result = &t
		}
	}
	return result
}

func TimeAdd(d time.Duration) *time.Time {
	t := time.Now().Add(d)
	return &t
}

func TruncateDate(toRound time.Time) time.Time {
	rounded := time.Date(toRound.Year(), toRound.Month(), toRound.Day(), 0, 0, 0, 0, toRound.Location())
	return rounded
}

func NewNearbyDayOfWeekAt(t *time.Time, dayOffWeek time.Weekday) *time.Time {
	for i := 1; i <= 7; i++ {
		t1 := t.AddDate(0, 0, -1)
		t = &t1
		if t.Weekday() == dayOffWeek {
			break
		}
	}
	return t
}

func NewNearbyDayOfMonthAt(t *time.Time, dayOffMonth int) *time.Time {
	ts := *t
	for i := 1; i <= 31; i++ {
		ts = ts.Add(-24 * time.Hour)
		if ts.Month() == t.Month() {
			if ts.Day() == dayOffMonth {
				break
			}
		} else {
			if ts.Day() == dayOffMonth {
				break
			}
			if ts.Day() < dayOffMonth {
				break
			}
		}
	}
	return &ts
}

func ToWorkHours(t1 *time.Time, t2 *time.Time) float64 {
	var workHours float64
	if t1.Unix() >= t2.Unix() {
		return 0
	}
	for t1.Unix() <= t2.Unix() {
		if t1.Weekday() != time.Sunday &&
			t1.Weekday() != time.Saturday {
			workHours += 8
		}
		t := t1.AddDate(0, 0, 1)
		t1 = &t
	}
	return workHours
}
