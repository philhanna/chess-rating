package chess

import (
	"regexp"
	"strings"
)

func Parse(html string) (*Rating, error) {
	html = MakeSingleLineFrom(html)
	scripts := ExtractScripts(html)
	for _, script := range scripts {
		/*
		if strings.HasPrefix(script, "window.chesscom.stats") {
			rating, err := ParseRating(script)
			return rating, err
		}
		*/
		_ = script
	}
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

func ExtractScripts(body string) []string {
	var (
		reStart = regexp.MustCompile(`<script[^>]*>(.*?)</script>`)
	)
	ms := reStart.FindAllStringSubmatch(body, -1)
	result := make([]string, 0)
	for _, m := range ms {
		result = append(result, strings.TrimSpace(m[1]))
	}
	return result	
}

func ExtractStatisticsJSONString(script string) string {
	return ""
}