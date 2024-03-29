package rating

import (
	"io"
	"net/http"
)

// GetHTML returns the HTML body from the specified URL
func GetHTML(url string) (*string, error) {
	resp, err := http.Get(url)
	if err != nil {
		return nil, err
	}
	body, _ := io.ReadAll(resp.Body)
	html := string(body)
	return &html, nil
}
