package helpers

import (
	"bytes"
	"encoding/json"
	"errors"
	"net/http"
)

func SlackHook(slackURL string, text string) error {
	bodyRequest, err := json.Marshal(map[string]interface{}{
		"text": text,
	})
	req, err := http.NewRequest("POST", slackURL, bytes.NewBuffer(bodyRequest))
	req.Header.Set("Content-Type", "application/json")
	client := &http.Client{}
	res, err := client.Do(req)
	if err != nil {
		return err
	}
	defer res.Body.Close()
	if res.StatusCode != http.StatusOK {
		return errors.New(res.Status)
	}
	return nil
}
