package backends

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"net/url"

	"github.com/czConstant/constant-budgeting-api/models"
)

type Client struct {
	BaseURL string
}

func (c *Client) doWithAuth(req *http.Request) (*http.Response, error) {
	client := &http.Client{}
	return client.Do(req)
}

func (c *Client) buildUrl(resourcePath string) string {
	if resourcePath != "" {
		return c.BaseURL + "/" + resourcePath
	}
	return c.BaseURL
}

func (c *Client) postJSON(apiURL string, headers map[string]string, jsonObject interface{}, result interface{}) error {
	bodyBytes, _ := json.Marshal(jsonObject)
	req, err := http.NewRequest(http.MethodPost, apiURL, bytes.NewBuffer(bodyBytes))
	if err != nil {
		return err
	}
	req.Header.Add("Content-Type", "application/json")
	for k, v := range headers {
		req.Header.Add(k, v)
	}
	resp, err := c.doWithAuth(req)
	if err != nil {
		return fmt.Errorf("failed request: %v", err)
	}
	if resp.StatusCode >= 300 {
		bodyBytes, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			return fmt.Errorf("http response bad status %d %s", resp.StatusCode, err.Error())
		}
		return fmt.Errorf("http response bad status %d %s", resp.StatusCode, string(bodyBytes))
	}
	if result != nil {
		return json.NewDecoder(resp.Body).Decode(result)
	}
	return nil
}

func (c *Client) getJSON(url string, result interface{}) (int, error) {
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return 0, fmt.Errorf("failed to create request: %v", err)
	}
	req.Header.Add("Content-Type", "application/json")
	resp, err := c.doWithAuth(req)
	if err != nil {
		return 0, fmt.Errorf("failed request: %v", err)
	}
	if resp.StatusCode >= 300 {
		bodyBytes, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			return resp.StatusCode, fmt.Errorf("http response bad status %d %s", resp.StatusCode, err.Error())
		}
		return resp.StatusCode, fmt.Errorf("http response bad status %d %s", resp.StatusCode, string(bodyBytes))
	}
	if result != nil {
		return resp.StatusCode, json.NewDecoder(resp.Body).Decode(result)
	}
	return resp.StatusCode, nil
}

func (c *Client) GetUserCheck(token string) (*models.User, int, error) {
	rs := struct {
		Result *models.User
	}{}
	resCode, err := c.getJSON(c.buildUrl(fmt.Sprintf("auth/check?token=%s", url.QueryEscape(token))), &rs)
	if err != nil {
		return nil, resCode, err
	}
	return rs.Result, resCode, nil
}

func (c *Client) GetAvailableBalance(token string) (uint64, error) {
	rs := struct {
		Result uint64
	}{}
	body := map[string]interface{}{}
	err := c.postJSON(c.buildUrl("/reserve/get-available-withdraw"),
		map[string]string{"Authorization": fmt.Sprintf("Bearer %s", token)}, body, &rs)
	if err != nil {
		return 0, err
	}
	return rs.Result, nil
}
