package chess

import "strings"

func Parse(html string) (*Rating, error) {
	return nil, nil
}

func MakeSingleLineFrom(html string) string {
	var length = len(html)

	sb := strings.Builder{}
	for i := 0; i < length; i++ {
		c := html[i]
		if c == '\r' || c == '\n' {
			c = ' '
		}
		sb.WriteByte(c)
	}

	return sb.String()
}