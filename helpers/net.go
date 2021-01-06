package helpers

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"io/ioutil"
	"net/http"

	"github.com/getsentry/raven-go"
)

func CurlURL(apiURL string, method string, headers map[string]string, postData interface{}, respData interface{}, debug bool) error {
	var err error
	defer func() {
		if debug &&
			err != nil {
			rvalStr := fmt.Sprintf("helpers.apiURL %s", err.Error())
			flags := map[string]string{
				"api_url": apiURL,
				"method":  method,
				"error":   err.Error(),
			}
			if postData != nil {
				var bodyBytes []byte
				bodyBytes, err = json.Marshal(postData)
				flags["post_data"] = string(bodyBytes)
			}
			raven.CaptureMessage(rvalStr, flags, raven.NewException(errors.New(rvalStr), raven.NewStacktrace(2, 3, nil)))
		}
	}()
	mt := http.MethodGet
	if method != "" {
		mt = method
	}
	var bytesBuffer io.Reader
	if postData != nil {
		var bodyBytes []byte
		bodyBytes, err = json.Marshal(postData)
		if err != nil {
			return err
		}
		bytesBuffer = bytes.NewBuffer(bodyBytes)
	}
	var req *http.Request
	req, err = http.NewRequest(mt, apiURL, bytesBuffer)
	if err != nil {
		return err
	}
	if len(headers) > 0 {
		for k, v := range headers {
			req.Header.Set(k, v)
		}
	} else {
		req.Header.Set("Content-Type", "application/json")
	}
	client := &http.Client{}
	var res *http.Response
	res, err = client.Do(req)
	if err != nil {
		return err
	}
	defer res.Body.Close()
	if res.StatusCode != http.StatusOK {
		var respBytes []byte
		respBytes, err = ioutil.ReadAll(res.Body)
		if err != nil {
			return err
		}
		err = fmt.Errorf("request is bad response status code %d ( %s )", res.StatusCode, string(respBytes))
		return err
	}
	if respData != nil {
		var respBytes []byte
		respBytes, err = ioutil.ReadAll(res.Body)
		if err != nil {
			return err
		}
		err = json.Unmarshal(respBytes, respData)
		if err != nil {
			return err
		}
	}
	return nil
}
