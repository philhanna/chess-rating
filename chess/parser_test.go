package chess

import (
	"os"
	"path/filepath"
	"runtime"
	"testing"

	"github.com/stretchr/testify/assert"
)

func getFileName(name string) string {
	_, b, _, _  := runtime.Caller(0)
	ProjectRoot := filepath.Dir(b)
	testdata := filepath.Join(ProjectRoot, "..", "testdata")
	filename := filepath.Join(testdata, name)
	return filename
}

func TestParse(t *testing.T) {
	tests := []struct {
		name    string
		html    string
		want    *Rating
		wantErr bool
	}{
		{
			html : func () string {
				filename := getFileName("chessdotcom.html")
				body, err := os.ReadFile(filename)
				assert.Nil(t, err)
				return string(body)
			}(),
			want : &Rating{
				UserID: "pehanna7",
				Rating: 805,
			},
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			rating, err := Parse(tt.html)
			if tt.wantErr {
				assert.NotNil(t, err)
			} else {
				assert.Nil(t, err)
				assert.Equal(t, tt.want, rating)
			}
		})
	}
}
