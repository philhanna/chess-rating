package chess

import "strings"

func Parse(html string) (*Rating, error) {
	return nil, nil
}

func MakeSingleLineFrom(body string) string {
	var length = len(body)

	sb := strings.Builder{}
	for i := 0; i < length; i++ {
		c := body[i]
		if c == '\r' || c == '\n' {
			c = ' '
		}
		sb.WriteByte(c)
	}

	return sb.String()
}
