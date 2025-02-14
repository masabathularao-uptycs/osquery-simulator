package main

import (
	"bufio"
	"bytes"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"flag"

	//"compress/zlib"
	//"compress/gzip"
	//"encoding/base64"
	"fmt"
	"io"
	"io/ioutil"

	//"compress/flate"
	"log"
	"math"
	"math/rand"
	"net"
	"net/http"
	"os"
	"sort"
	"strconv"
	"strings"
	"sync"

	//"reflect"
	"time"

	_ "net/http/pprof"

	//"github.com/pkg/profile"

	"github.com/gin-gonic/gin"
	//"github.com/gin-contrib/gzip"
	//"github.com/nanmu42/gzip"
	uuid "github.com/nu7hatch/gouuid"
	"github.com/rafaeldias/async"
)

var enrollClients []*http.Client
var configClients []*http.Client
var logClients []*http.Client
var distReadClients []*http.Client

//var json = jsoniter.ConfigCompatibleWithStandardLibrary

// controlls the speed of actions
var enrollbatchsize = 400
var configbatchsize = 400
var distributedreadhbatchsize = 400
var print_timer_sleep_time = 120 //seconds
var assets_per_log_channel = 50
var log_channels []chan LogGoRoutineMsg
var num_log_channels int

var config_channel_count = 100
var config_channels []chan ConfigRequest

var allow_reads = true
var dist_read_channel_count = 5000
var dist_read_channels []chan DistReadRequest

// flags -- do not use. use corresponding vars. func init parses these
var domain_flag = flag.String("domain", "", "Uptycs domain")
var secret_flag = flag.String("secret", "", "Customer secret for the domain")
var name_flag = flag.String("name", "", "Name file to be used for assets")
var port_flag = flag.String("port", "", "Port to run gin server on to recieve python messages")
var count_flag = flag.Int("count", 0, "Number of assets to bring up in the process")

// variables used by nodejs simulator
var random_names []string
var random_uuids []string
var node_key *sync.Map
var counter_mux sync.Mutex
var enroll_fail_counter int
var enroll_histogram Histogram
var enroll_histogram_mux sync.Mutex
var config_histogram Histogram
var config_histogram_mux sync.Mutex
var log_histogram Histogram
var log_histogram_mux sync.Mutex
var log_fail_counter int
var config_fail_counter int
var dist_read_fail_counter int
var dist_read_histogram Histogram
var dist_read_mux sync.Mutex
var dist_write_fail_counter int
var dist_write_histogram Histogram
var dist_write_mux sync.Mutex
var reenroll_count int
var enrollurl string
var configurl string
var logurl string
var distributedreadurl string
var distributedwriteurl string

// get values instead of pointers from flags
var domain = ""
var secret = ""
var name = ""
var port = ""
var count = 0
var ca = ""
var platform_info = make_platform_info()
var caCertPool = x509.NewCertPool()

var configInterval time.Duration
var distInterval time.Duration
var enrollReqTimeout time.Duration
var configDistInterval time.Duration
var enrollDistInterval time.Duration
var distributedDistInterval time.Duration
var dist_write_status = make(map[string]string)
var dist_write_table []map[string]string

type ConfigRequest struct {
	NodeKey    string
	Index      int
	HttpChan   chan *HttpResponse
	HttpClient *http.Client
}

type DistReadRequest struct {
	Index      int
	HttpChan   chan *HttpResponse
	HttpClient *http.Client
}

type HttpResponse struct {
	url      string
	response *http.Response
	err      error
}

func generate_enroll_body(host_name, uuidv4 string) AutoGenerated {
	ov := make_os_version(host_name)
	osqi := make_osquery_info(uuidv4)
	si := make_system_info(host_name, uuidv4)
	hd := HostDetails{
		OsVersion:    ov,
		OsqueryInfo:  osqi,
		SystemInfo:   si,
		PlatformInfo: platform_info,
	}
	return AutoGenerated{
		//EnrollSecret: "2887a6da-df43-46fa-b6db-5a9d8da09cc4##2887a6da-df43-46fa-b6db-5a9d8da09cc4", // auto
		//EnrollSecret:   "19fe4fff-ab86-4264-8fba-dc8eea1ad6ef##19fe4fff-ab86-4264-8fba-dc8eea1ad6ef",
		EnrollSecret:   secret,
		HostIdentifier: uuidv4,
		PlatformType:   9,
		HostDetails:    hd,
	}

}

type ConfigMsg struct {
	NodeKey string `json:"node_key"`
}

type AutoGenerated struct {
	EnrollSecret   string      `json:"enroll_secret"`
	HostIdentifier string      `json:"host_identifier"`
	PlatformType   int         `json:"platform_type"`
	HostDetails    HostDetails `json:"host_details"`
}
type OsVersion struct {
	ID           string `json:"_id"`
	Codename     string `json:"codename"`
	Major        string `json:"major"`
	Minor        string `json:"minor"`
	Name         string `json:"name"`
	Patch        string `json:"patch"`
	Platform     string `json:"platform"`
	PlatformLike string `json:"platform_like"`
	Version      string `json:"version"`
}

func make_os_version(hostname string) OsVersion {
	return OsVersion{
		ID:           hostname,
		Codename:     "jammy",
		Major:        "22",
		Minor:        "4",
		Name:         "Ubuntu",
		Patch:        "4",
		Platform:     "ubuntu",
		PlatformLike: "debian",
		Version:      "22.04.4",
	}
}

type OsqueryInfo struct {
	BuildDistro   string `json:"build_distro"`
	BuildPlatform string `json:"build_platform"`
	ConfigHash    string `json:"config_hash"`
	ConfigValid   string `json:"config_valid"`
	Extensions    string `json:"extensions"`
	InstanceID    string `json:"instance_id"`
	Pid           string `json:"pid"`
	StartTime     string `json:"start_time"`
	Uuidv4        string `json:"uuidv4"`
	Version       string `json:"version"`
	Watcher       string `json:"watcher"`
}

func make_osquery_info(uuidv4 string) OsqueryInfo {
	uuid, uerr := uuid.NewV4()
	if uerr != nil {
		log.Fatalf("Got error generating uuid: %v", uerr)
	}
	return OsqueryInfo{
		BuildDistro:   "xenial",
		BuildPlatform: "ubuntu",
		ConfigHash:    "",
		ConfigValid:   "0",
		Extensions:    "active",
		InstanceID:    uuid.String(),
		Pid:           "121",
		StartTime:     "1710429552",
		Uuidv4:        uuidv4,
		Version:       "5.11.0-Uptycs",
		Watcher:       "175",
	}
}

type PlatformInfo struct {
	Address    string `json:"address"`
	Date       string `json:"date"`
	Extra      string `json:"extra"`
	Revision   string `json:"revision"`
	Size       string `json:"size"`
	Vendor     string `json:"vendor"`
	Version    string `json:"version"`
	VolumeSize string `json:"volume_size"`
}

func make_platform_info() PlatformInfo {
	return PlatformInfo{
		Address:    "0xf000",
		Date:       "07/07/2016",
		Extra:      "",
		Revision:   "1.12",
		Size:       "16777216",
		Vendor:     "HP",
		Version:    "N82 Ver. 01.12",
		VolumeSize: "0",
	}
}

type SystemInfo struct {
	ComputerName     string `json:"computer_name"`
	Hostname         string `json:"hostname"`
	LocalHostname    string `json:"local_hostname"`
	CPUBrand         string `json:"cpu_brand"`
	CPULogicalCores  string `json:"cpu_logical_cores"`
	CPUPhysicalCores string `json:"cpu_physical_cores"`
	CPUSubtype       string `json:"cpu_subtype"`
	CPUType          string `json:"cpu_type"`
	HardwareModel    string `json:"hardware_model"`
	HardwareSerial   string `json:"hardware_serial"`
	HardwareVendor   string `json:"hardware_vendor"`
	HardwareVersion  string `json:"hardware_version"`
	PhysicalMemory   string `json:"physical_memory"`
	UUID             string `json:"uuid"`
}

func make_system_info(host_name, uuidv4 string) SystemInfo {
	return SystemInfo{
		ComputerName:     host_name,
		Hostname:         host_name,
		LocalHostname:    host_name,
		CPUBrand:         "Intel(R) Core(TM) i7-6700HQ CPU @ 2.60GHz\u0000\u0000\u0000\u0000\u0000\u0000\u0000",
		CPULogicalCores:  "8",
		CPUPhysicalCores: "8",
		CPUSubtype:       "94",
		CPUType:          "6",
		HardwareModel:    "HP ZBook Studio G3",
		HardwareSerial:   "CND60233F6",
		HardwareVendor:   "HP",
		HardwareVersion:  "",
		PhysicalMemory:   "25199255552",
		UUID:             uuidv4,
	}
}

type HostDetails struct {
	OsVersion    OsVersion    `json:"os_version"`
	OsqueryInfo  OsqueryInfo  `json:"osquery_info"`
	PlatformInfo PlatformInfo `json:"platform_info"`
	SystemInfo   SystemInfo   `json:"system_info"`
}

type DistributedWriteBody struct {
	Queries map[string]map[string]interface{} `json:"queries"`
}

type LogMessage struct {
	NodeKey string                   `json:"node_key"`
	LogType string                   `json:"log_type"`
	Data    []map[string]interface{} `json:"data"`
}

type LogGoRoutineMsg struct {
	ToPost []byte
	Client *http.Client
}

func NewLogMessage(node_key string, obj []map[string]interface{}) LogMessage {
	return LogMessage{
		NodeKey: node_key,
		LogType: "result",
		Data:    obj,
	}
}

type distReadReq struct {
	NodeKey string `json:"node_key"`
}

type Histogram struct {
	Records []float32
}

func (h *Histogram) add(val float32, m *sync.Mutex) {
	m.Lock()
	h.Records = append(h.Records, val)
	m.Unlock()
}

func (h Histogram) min() float32 {
	if len(h.Records) == 0 {
		return float32(0)
	} else {
		m := h.Records[0]
		for _, val := range h.Records {
			if val < m {
				m = val
			}
		}
		return m
	}
}

func (h Histogram) max() float32 {
	if len(h.Records) == 0 {
		return float32(0)
	} else {
		m := h.Records[0]
		for _, val := range h.Records {
			if val > m {
				m = val
			}
		}
		return m
	}
}

func (h Histogram) mean() float32 {
	if len(h.Records) == 0 {
		return float32(0)
	} else {
		c := 0
		s := float32(0)
		for _, val := range h.Records {
			c += 1
			s += val
		}
		return s / float32(c)
	}
}

func format_starts(h Histogram) string {
	return fmt.Sprintf("Min: %v, Max: %v, Mean: %v, Median: %v", h.min(),
		h.max(), h.mean(), h.median())
}

type ByFloat []float32

func (a ByFloat) Len() int           { return len(a) }
func (a ByFloat) Swap(i, j int)      { a[i], a[j] = a[j], a[i] }
func (a ByFloat) Less(i, j int) bool { return a[i] < a[j] }

func (h Histogram) median() float32 {
	if len(h.Records) == 0 {
		return float32(0)
	} else {
		sort.Sort(ByFloat(h.Records))
		l := len(h.Records)
		if l%2 == 0 {
			left_ele := math.Floor(float64(l)/2 - 1)
			right_ele := math.Floor(float64(l) / 2)
			s := h.Records[int(left_ele)] + h.Records[int(right_ele)]
			return float32(s / 2)
		} else {
			pos := math.Floor(float64(l) / 2)
			return h.Records[int(pos)]
		}

	}
}

func localize_syncmap(m *sync.Map) map[interface{}]interface{} {
	s := make(map[interface{}]interface{})
	m.Range(func(k, v interface{}) bool {
		s[k] = v
		return true
	})
	return s
}

func get_node_key(i int) string {
	m := localize_syncmap(node_key)
	if val, ok := m[i]; ok {
		k := val.(string)
		return k
	} else {
		return ""
	}
}

func log_msg_listener(c chan LogGoRoutineMsg) {
	for msg := range c {
		log_goroutine(msg.ToPost, msg.Client)
	}
}

/*
func enroll_goroutine(url string, i int, ch chan *HttpResponse, client *http.Client) {
	ee := generate_enroll_body(random_names[i], random_uuids[i])
	eej, err := json.Marshal(ee)
        fmt.Println(i)
        fmt.Println(ee)
        fmt.Println(eej)
        fmt.Println(url)
	start_req := time.Now()
        fmt.Println(bytes.NewBuffer(eej))
	resp, err := client.Post(url, "application/json", bytes.NewBuffer(eej))
        //fmt.Println(resp)
	elapsed := time.Since(start_req).Milliseconds()
	enroll_histogram.add(float32(elapsed), &enroll_histogram_mux)
	 if err != nil {
	   log.Fatalln(err)
	      }
	var tesult map[string]interface{}
        fmt.Println("=======")
	json.NewDecoder(resp.Body).Decode(&tesult)
        fmt.Println("=======")
        fmt.Println(tesult)
	if tesult["node_invalid"] == false {
		key := tesult["node_key"].(string)
		node_key.Store(i, key)

	}
	resp.Body.Close()
	ch <- &HttpResponse{url, resp, err}
}
*/

func enroll_goroutine(url string, i int, ch chan *HttpResponse, client *http.Client) {
	ee := generate_enroll_body(random_names[i], random_uuids[i])
	eej, err := json.Marshal(ee)
	//fmt.Println(i)
	//fmt.Println(ee)
	//fmt.Println(eej)
	//fmt.Println(url)
	start_req := time.Now()
	//fmt.Println(bytes.NewBuffer(eej))
	reqt, err := http.NewRequest("POST", url, bytes.NewBuffer(eej))
	reqt.Header.Set("Content-type", "application/json")
	reqt.Header.Set("User-Agent", "osquery/5.11.0.8-Uptycs")
	resp, errs := client.Do(reqt)
	//      resp, err := client.Post(url, "application/json", bytes.NewBuffer(eej))
	//fmt.Println(resp)
	elapsed := time.Since(start_req).Milliseconds()
	enroll_histogram.add(float32(elapsed), &enroll_histogram_mux)
	if errs != nil {
		log.Fatalln("errs", errs)
	}
	if err != nil {
		log.Fatalln(err)
	}
	var tesult map[string]interface{}
	//fmt.Println("=======")
	json.NewDecoder(resp.Body).Decode(&tesult)
	//fmt.Println("=======")
	//fmt.Println(tesult)
	if tesult["node_invalid"] == false {
		key := tesult["node_key"].(string)
		node_key.Store(i, key)

	}
	resp.Body.Close()
	ch <- &HttpResponse{url, resp, err}
}

func sendEnroll(url string) []*HttpResponse {
	ch := make(chan *HttpResponse, count) // buffered
	responses := []*HttpResponse{}
	for i := 0; i < count; i++ {
		if i%enrollbatchsize == 0 {
			time.Sleep(1 * time.Second)
		}
		time.Sleep(1 * time.Nanosecond)

		go enroll_goroutine(enrollurl, i, ch, get_enroll_client(i))
	}

	for {
		select {
		case r := <-ch:
			// fmt.Printf("%s was fetched\n", r.url)
			responses = append(responses, r)
			if len(responses) == count {
				return responses
			}
		case <-time.After(150 * time.Second):
			fmt.Printf(".")
		}
	}
}

func enroll() {
	var wg sync.WaitGroup
	wg.Add(1)
	results := sendEnroll(enrollurl)
	for index, result := range results {
		if result.response.Status != "200 OK" {
			enroll_fail_counter += 1
			log.Println("Failed enrolling index", index)
		} else {
			if index%50 == 0 || index == (count-1) {
				log.Println("Successfully enrolled", index)
			}
		}
	}
	time.Sleep(5 * time.Second)
	go genconfig()
	wg.Wait()
}

func genconfig() {
	sum := 0
	for {
		sum++ // repeated forever
		//fmt.Println("sum",sum)
		conresults := sendConfig(configurl)
		for index, result := range conresults {
			// fmt.Printf("%d,%s status: %s\n", a, result.url,
			// 	result.response.Status)
			if result.response.Status != "200 OK" {
				config_fail_counter += 1
				log.Println("Failed config for", random_names[index])
			}
		}
		if sum == 1 && allow_reads {
			fmt.Println("\nstart distributed read go routine")
			go distributed()
		}
		time.Sleep(configInterval * time.Second)
	}
}

/*
func dist_read_listener(c chan DistReadRequest) {
	for distMsg := range c {
		node_key := get_node_key(distMsg.Index)

		client := distMsg.HttpClient
		ee := &distReadReq{NodeKey: node_key}
		eej, err := json.Marshal(ee)
		req, brr := http.NewRequest("POST", distributedreadurl, bytes.NewBuffer(eej))
		if brr != nil {
			log.Fatal("Error reading request. ", brr)
		}
		// Set headers
		req.Header.Set("Content-Type", "application/json")

		//resp, err := client.Post(url, "application/json", bytes.NewBuffer(eej))
		//fmt.Println("request header Status============:", req.Header)
		start_req := time.Now()
		resp, err := client.Do(req)
		if err != nil {
			log.Fatal("Error reading response. ", err)
		}

		elapsed := time.Since(start_req).Milliseconds()

		dist_read_histogram.add(float32(elapsed), &config_histogram_mux)

		var outer map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&outer)
		resp.Body.Close()
		if len(outer) > 0 {
			for key, value := range outer {
				if key == "queries" {
					query_map := value.(map[string]interface{})
					for query, _ := range query_map {
						query_portion := make(map[string]interface{})
						to_respond := make(map[string]interface{})
						query_portion[query] = dist_write_table
						to_respond["queries"] = query_portion
						to_respond["node_key"] = node_key
						to_respond["statuses"] = dist_write_status
						response_body, err := json.Marshal(to_respond)
						if err != nil {
							log.Fatalf("Got distributed_write error %s", err)
						}
						start_dw := time.Now()
						dw, dw_e := client.Post(distributedwriteurl, "application/json", bytes.NewBuffer(response_body))
						if dw_e != nil {
							log.Fatalf("Got distributed write error %s", dw_e)
						}
						dw_elapsed := time.Since(start_dw).Milliseconds()
						dist_write_histogram.add(float32(dw_elapsed), &dist_write_mux)
						if dw.Status != "200 OK" {
							dist_write_fail_counter += 1
							log.Println("Failed distributed_write for index", distMsg.Index)
						}
						json.NewDecoder(dw.Body).Decode(&resp)
						dw.Body.Close()
					}
				}
			}
		}
		scanner := bufio.NewScanner(resp.Body)
		scanner.Split(bufio.ScanBytes)
		for scanner.Scan() {
			fmt.Print(scanner.Text())
		}
		distMsg.HttpChan <- &HttpResponse{distributedreadurl, resp, err}
	}
}
*/

func dist_read_listener(c chan DistReadRequest) {
	for distMsg := range c {
		node_key := get_node_key(distMsg.Index)
		//fmt.Println("node_key",node_key,"daya",distMsg.Index)
		client := distMsg.HttpClient
		//fmt.Println("client",client,distributedreadurl)
		ee := &distReadReq{NodeKey: node_key + ":" + random_names[distMsg.Index]}
		eej, err := json.Marshal(ee)
		req, brr := http.NewRequest("POST", distributedreadurl, bytes.NewBuffer(eej))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("User-Agent", "osquery/4.6.6.18-Uptycs")
		req.Header.Set("Accept", "application/json")

		if brr != nil {
			log.Fatal("Error reading request. brr", brr)
		}
		// Set headers
		//fmt.Println(req)
		start_req := time.Now()
		resp, err := client.Do(req)
		if err != nil {
			log.Fatal("Error reading response. err", err)
			continue
		}
		elapsed := time.Since(start_req).Milliseconds()

		dist_read_histogram.add(float32(elapsed), &config_histogram_mux)

		var outer map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&outer)
		resp.Body.Close()
		if len(outer) > 0 {
			for key, value := range outer {
				if key == "queries" {
					//fmt.Println("key", key, "value", value)
					query_map := value.(map[string]interface{})
					//for query, _ := range query_map {
					for queryId, queryValue := range query_map {
						// Assert that queryValue is a string (the actual SQL query)
						query, _ := queryValue.(string) // Added this type assertion and 'ok' check
						to_respond := make(map[string]interface{})
						//fmt.Println("query:", query)

						if strings.Contains(query, "uptycs_edr_linux_mitre") {
							var dist_write_status = make(map[string]int)
							var dist_write_message = make(map[string]string)
							query_portion := make(map[string]interface{})
							dist_write_table_data := set_dist_write_stats_mitre()
							query_portion[queryId] = dist_write_table_data
							dist_write_status[queryId] = 0
							to_respond["queries"] = query_portion
							to_respond["node_key"] = node_key + ":" + random_names[distMsg.Index]
							to_respond["statuses"] = dist_write_status
							dist_write_message[queryId] = "OK"
							to_respond["messages"] = dist_write_message
						} else if strings.Contains(query, "nginx") {
							var dist_write_status = make(map[string]int)
							var dist_write_message = make(map[string]string)
							query_portion := make(map[string]interface{})
							dist_write_table_data := set_dist_write_stats()
							query_portion[queryId] = dist_write_table_data
							dist_write_status[queryId] = 0
							to_respond["queries"] = query_portion
							to_respond["node_key"] = node_key + ":" + random_names[distMsg.Index]
							to_respond["statuses"] = dist_write_status
							dist_write_message[queryId] = "OK"
							to_respond["messages"] = dist_write_message
						} else if strings.Contains(query, "OpenShift") {
							var dist_write_status = make(map[string]int)
							var dist_write_message = make(map[string]string)
							query_portion := make(map[string]interface{})
							dist_write_table_data := set_dist_write_stats_openshift()
							query_portion[queryId] = dist_write_table_data
							dist_write_status[queryId] = 0
							to_respond["queries"] = query_portion
							to_respond["node_key"] = node_key + ":" + random_names[distMsg.Index]
							to_respond["statuses"] = dist_write_status
							dist_write_message[queryId] = "OK"
							to_respond["messages"] = dist_write_message
						} else if strings.Contains(query, "nginx") && !strings.Contains(query, "ubuntu") && !strings.Contains(query, "yara") {
							var dist_write_status = make(map[string]int)
							var dist_write_message = make(map[string]string)
							query_portion := make(map[string]interface{})
							dist_write_table_data := set_dist_write_stats_ubuntu()
							query_portion[queryId] = dist_write_table_data
							dist_write_status[queryId] = 0
							to_respond["queries"] = query_portion
							to_respond["node_key"] = node_key + ":" + random_names[distMsg.Index]
							to_respond["statuses"] = dist_write_status
							dist_write_message[queryId] = "OK"
							to_respond["messages"] = dist_write_message
						} else if strings.Contains(query, "k8osquery") {
							var dist_write_status = make(map[string]int)
							var dist_write_message = make(map[string]string)
							query_portion := make(map[string]interface{})
							dist_write_table_data := set_dist_write_stats_k8osquery()
							query_portion[queryId] = dist_write_table_data
							dist_write_status[queryId] = 0
							to_respond["queries"] = query_portion
							to_respond["node_key"] = node_key + ":" + random_names[distMsg.Index]
							to_respond["statuses"] = dist_write_status
							dist_write_message[queryId] = "OK"
							to_respond["messages"] = dist_write_message
						} else if strings.Contains(query, "yara") {
							var dist_write_status = make(map[string]int)
							var dist_write_message = make(map[string]string)
							query_portion := make(map[string]interface{})
							dist_write_table_data := set_dist_write_stats_yara()
							query_portion[queryId] = dist_write_table_data
							dist_write_status[queryId] = 0
							to_respond["queries"] = query_portion
							to_respond["node_key"] = node_key + ":" + random_names[distMsg.Index]
							to_respond["statuses"] = dist_write_status
							dist_write_message[queryId] = "OK"
							to_respond["messages"] = dist_write_message
						} else {
							var dist_write_status = make(map[string]int)
							var dist_write_message = make(map[string]string)
							query_portion := make(map[string]interface{})
							query_portion[query] = dist_write_table
							dist_write_status[queryId] = 0
							to_respond["queries"] = query_portion
							to_respond["node_key"] = node_key + ":" + random_names[distMsg.Index]
							to_respond["statuses"] = dist_write_status
							dist_write_message[queryId] = "OK"
							to_respond["messages"] = dist_write_message
						}

						//fmt.Println("to_respond:", to_respond)
						response_body, err := json.Marshal(to_respond)
						if err != nil {
							log.Fatalf("Got distributed_write error %s", err)
						}
						start_dw := time.Now()
						// dw, dw_e := client.Post(distributedwriteurl, "application/json", bytes.NewBuffer(response_body))
						// if dw_e != nil {
						// 	log.Fatalf("Got distributed write error %s", dw_e)
						// }
						// dw_elapsed := time.Since(start_dw).Milliseconds()
						// dist_write_histogram.add(float32(dw_elapsed), &dist_write_mux)
						// if dw.Status != "200 OK" {
						// 	dist_write_fail_counter += 1
						// 	log.Println("Failed distributed_write for index", distMsg.Index)
						// 	log.Println("Response body:", string(response_body))
						// 	log.Println("Response body dw:", dw)
						// }
						// json.NewDecoder(dw.Body).Decode(&resp)
						// dw.Body.Close()
						req1, _ := http.NewRequest("POST", distributedwriteurl, bytes.NewBuffer(response_body))
						req1.Header.Set("Content-Type", "application/json")
						req1.Header.Set("User-Agent", "osquery/4.6.4.8-Uptycs")
						req1.Header.Set("Accept", "application/json")
						resp1, dw_e := client.Do(req1)
						//log.Println("resp1", resp1)
						if dw_e != nil {
							log.Fatalf("Got distributed write error %s", dw_e)
						}
						dw_elapsed := time.Since(start_dw).Milliseconds()
						dist_write_histogram.add(float32(dw_elapsed), &dist_write_mux)
						//realtime_resp_counter += 1
						//log.Println("post error", dw_e)
						if resp1.Status != "200 OK" {
							dist_write_fail_counter += 1
							//realtime_resp_fail_counter += 1
							log.Println("Failed distributed_write for index", distMsg.Index)
						}
						json.NewDecoder(resp1.Body).Decode(&resp)
						resp1.Body.Close()
					}
				}
			}
		}
		scanner := bufio.NewScanner(resp.Body)
		scanner.Split(bufio.ScanBytes)
		for scanner.Scan() {
			fmt.Print(scanner.Text())
		}
		distMsg.HttpChan <- &HttpResponse{distributedreadurl, resp, err}
	}
}

func config_listener(c chan ConfigRequest) {
	for CR := range c {
		config_goroutine(CR.NodeKey, CR.Index, CR.HttpChan, CR.HttpClient)
	}
}

/*
func config_goroutine(node_key string, i int, http_chan chan *HttpResponse, client *http.Client) {
	ee := &ConfigMsg{NodeKey: node_key}
	eej, err := json.Marshal(ee)
	start_req := time.Now()
	resp, err := client.Post(configurl, "application/json", bytes.NewBuffer(eej))

	elapsed := time.Since(start_req).Milliseconds()

	config_histogram.add(float32(elapsed), &config_histogram_mux)

	var tesult map[string]interface{}
	//log.Println("Status code:", resp.Status)
	if resp.Status != "200 OK" {
		json.NewDecoder(resp.Body).Decode(&tesult)
		if tesult["node_invalid"] == true {
			ch := make(chan *HttpResponse)
			fmt.Println("\nPlease re-enroll asset id", i)
			go enroll_goroutine(enrollurl, i, ch, get_enroll_client(i))
			fmt.Println("Send re-enroll request")
		}
	}
	resp.Body.Close()
	http_chan <- &HttpResponse{configurl, resp, err}

}
*/

func config_goroutine(node_key string, i int, http_chan chan *HttpResponse, client *http.Client) {
	//fmt.Println("node in config",node_key)
	ee := &ConfigMsg{NodeKey: node_key}
	eej, err := json.Marshal(ee)
	start_req := time.Now()
	reqt, err := http.NewRequest("POST", configurl, bytes.NewBuffer(eej))
	//resp, err := client.Post(configurl, "application/json", bytes.NewBuffer(eej))
	reqt.Header.Set("Content-type", "application/json")
	reqt.Header.Set("User-Agent", "osquery/4.6.4.8-Uptycs")
	resp, errs := client.Do(reqt)
	elapsed := time.Since(start_req).Milliseconds()
	if errs != nil {
		log.Fatalln("errs", errs)
	}

	config_histogram.add(float32(elapsed), &config_histogram_mux)

	var tesult map[string]interface{}
	//log.Println("Status code:", resp.Status)
	if resp.Status != "200 OK" {
		json.NewDecoder(resp.Body).Decode(&tesult)
		if tesult["node_invalid"] == true {
			ch := make(chan *HttpResponse)
			fmt.Println("\nPlease re-enroll asset id", i)
			go enroll_goroutine(enrollurl, i, ch, get_enroll_client(i))
			fmt.Println("Send re-enroll request")
		}
	}
	resp.Body.Close()
	http_chan <- &HttpResponse{configurl, resp, err}

}

func sendConfig(url string) []*HttpResponse {
	ch := make(chan *HttpResponse, count) // buffered
	responses := []*HttpResponse{}
	for i := 0; i < count; i++ {
		if i%configbatchsize == 0 {
			time.Sleep(1 * time.Second)
		}
		time.Sleep(1 * time.Nanosecond)
		target := config_channels[i%config_channel_count]
		target <- ConfigRequest{NodeKey: get_node_key(i), Index: i, HttpChan: ch,
			HttpClient: get_config_client(i)}
	}

	for {
		select {
		case r := <-ch:
			responses = append(responses, r)
			if len(responses) == count {
				return responses
			}
		case <-time.After(150 * time.Second):
			fmt.Printf(".")
		}
	}
}

func distributed() {
	for {
		//fmt.Println("I am inside distributed")
		conresults := distributed_read()
		for index, result := range conresults {
			// fmt.Printf("%d,%s status: %s\n", a, result.url,
			// 	result.response.Status)
			if result.response.Status != "200 OK" {
				dist_read_fail_counter += 1
				log.Println("Failed dist read for", random_names[index])
			}
		}
		time.Sleep(distributedDistInterval * time.Second)
	}
}

func parse_names() {
	file, err := os.Open(name)
	if err != nil {
		log.Fatalf("Could not open file %s", name)
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	name_count := 0
	for scanner.Scan() {
		if name_count < count {
			random_names = append(random_names, scanner.Text())
			uuid, uerr := uuid.NewV4()
			if uerr != nil {
				log.Fatalf("Got error generating uuid: %v", uerr)
			}

			random_uuids = append(random_uuids, strings.ToUpper(uuid.String()))
			name_count += 1
		} else {
			break
		}

	}
	if err := scanner.Err(); err != nil {
		log.Fatal(err)
	}
}

func post_to_logger(tstamp, name, uuidv4, node_key string, jsonMap LogMessage, client *http.Client, index int) {
	jsonMap.NodeKey = node_key
	for _, data := range jsonMap.Data {
		if _, ok := data["hostIdentifier"]; ok {
			data["hostIdentifier"] = uuidv4
		} else {
			fmt.Println("No hostIdentifier in data")
		}

		if _, ok := data["unixTime"]; ok {
			tstamp_int, tstamp_err := strconv.ParseInt(tstamp, 10, 32)
			if tstamp_err != nil {
				panic(tstamp_err)
			}
			data["unixTime"] = tstamp_int
		}

		// if columnData, ok := data["columns"].(map[string]interface{}); ok {
		// 	if _, exists := columnData["login_name"]; exists {
		// 		log.Println("login_name exists")
		// 		const letters = "abcdefghijklmnopqrstuvwxyz"
		// 		rand.Seed(time.Now().UnixNano()) // Seed the random number generator
		// 		word := make([]byte, 6)
		// 		for i := range word {
		// 			word[i] = letters[rand.Intn(len(letters))]
		// 		}
		// 		log.Println("new login_name:", string(word))
		// 		columnData["login_name"] = string(word)
		// 	}
		// }

		if rowData, ok := data["columns"]; ok {
			//log.Println("columns exists in data")
			if columnData, ok := rowData.(map[string]interface{}); ok {
				//log.Println("checking for event_time data")
				if _, exists := columnData["event_time"]; exists {
					//log.Println("event_time exists in data")
					//log.Println(strconv.Itoa(int(time.Now().UnixMilli())))
					data["columns"].(map[string]interface{})["event_time"] = strconv.Itoa(int(time.Now().UnixMilli()))
				}
				// else {
				// 	log.Println("event_time does not exists")
				// }
			}
		}

		if rowData, ok := data["columns"]; ok {
			//log.Println("columns exists in data")
			if columnData, ok := rowData.(map[string]interface{}); ok {
				//log.Println("checking for login_name data")
				const letters = "abcdefghijklmnopqrstuvwxyz"
				rand.Seed(time.Now().UnixNano()) // Seed the random number generator
				word := make([]byte, 10)
				for i := range word {
					word[i] = letters[rand.Intn(len(letters))]
				}
				//log.Println("new login_name:", string(word))
				if _, exists := columnData["login_name"]; exists {
					//log.Println("login_name exists in data")
					data["columns"].(map[string]interface{})["login_name"] = string(word) + name
				}
				// else {
				// 	log.Println("login_name does not exists")
				// }
			}
		}

		if _, ok := data["hostname"]; ok {
			data["hostname"] = name
		}

		if _, ok := data["snapshot"]; ok {
			snd := data["snapshot"].([]interface{})
			for _, val := range snd {
				converted := val.(map[string]interface{})
				if _, ok := converted["hostname"]; ok {
					converted["hostname"] = name
				}
			}
		}
	}

	msg_json, unmarshalErr := json.Marshal(jsonMap)
	if unmarshalErr != nil {
		log.Fatalf(unmarshalErr.Error())
	}
	target := log_channels[index%num_log_channels]
	target <- LogGoRoutineMsg{ToPost: msg_json, Client: client}

}

/*

func gzipWrite(w io.Writer, data []byte) error {
        // Write gzipped data to the client
        gw, err := gzip.NewWriterLevel(w, gzip.BestSpeed)
        defer gw.Close()
        gw.Write(data)
        return err
}

*/

func log_goroutine(to_post []byte, cli *http.Client) {
	//fmt.Println("to_post",string(to_post))

	start_req := time.Now()
	//fmt.Println(ect.TypeOf(to_post))
	resp, postErr := cli.Post(logurl, "application/json", bytes.NewBuffer(to_post))
	//resp, postErr := cli.Post(logurl, "application/json", bytes.NewBufferString(bufe.String()))
	if postErr != nil {
		log.Fatalf(postErr.Error())
	}
	resp.Header.Set("Content-Encoding", "gzip")
	elapsed := time.Since(start_req).Milliseconds()
	log_histogram.add(float32(elapsed), &log_histogram_mux)

	var result map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&result)
	//fmt.Println(result)
	//fmt.Println(resp)
	if resp.Status != "200 OK" {
		log.Println("bad status code from log")
		log_fail_counter += 1
	}
	resp.Body.Close()

}

func single_threaded_log(tstamp string, jsonMap LogMessage) {
	for index, name := range random_names {
		uuidv4 := random_uuids[index]
		post_to_logger(tstamp, name, uuidv4, get_node_key(index), jsonMap, logClients[index], index)
	}
}

func distributed_read() []*HttpResponse {
	ch := make(chan *HttpResponse, count) // buffered
	responses := []*HttpResponse{}
	for i := 0; i < count; i++ {
		if i%distributedreadhbatchsize == 0 {
			time.Sleep(1 * time.Second)
		}
		time.Sleep(1 * time.Nanosecond)
		target := dist_read_channels[i%dist_read_channel_count]
		target <- DistReadRequest{Index: i, HttpChan: ch, HttpClient: get_distributed_client(i)}

	}

	for {
		select {
		case r := <-ch:
			responses = append(responses, r)
			if len(responses) == count {
				return responses
			}
		case <-time.After(150 * time.Second):
			fmt.Printf(".")
		}
	}

}

func post_message(c *gin.Context) {

	l := c.Request.ContentLength

	buf := make([]byte, l)
	res := ""
	for {
		n, err := c.Request.Body.Read(buf)
		res += string(buf[:n])
		if err == io.EOF {
			break
		}

	}

	tstamp := res[0:10]
	//fmt.Println("tstamp",tstamp)
	//fmt.Println(res[10:])
	var jsonMap LogMessage
	err := json.Unmarshal([]byte(res[10:]), &jsonMap)
	if err != nil {
		panic(err)
	}

	c.JSON(200, gin.H{})
	single_threaded_log(tstamp, jsonMap)
}

// func set_dist_write_stats() {
// 	dist_write_status["info"] = "0"
// 	m := make(map[string]string)
// 	m["days"] = "60"
// 	m["hours"] = "7"
// 	m["minutes"] = "29"
// 	m["seconds"] = "5"
// 	m["total_seconds"] = "5210945"
// 	dist_write_table = append(dist_write_table, m)
// }

func set_dist_write_stats() []map[string]string {
	var dist_write_table []map[string]string
	m := make(map[string]string)
	// m["domain"] = fmt.Sprintf("%v",domain_flag)
	m["tag"] = "nginx"
	dist_write_table = append(dist_write_table, m)
	return dist_write_table
}

func set_dist_write_stats_mitre() []map[string]string {
	var dist_write_table []map[string]string
	m := make(map[string]string)
	// m["domain"] = fmt.Sprintf("%v",domain_flag)
	m["tag"] = "uptycs_edr_linux_mitre"
	dist_write_table = append(dist_write_table, m)
	return dist_write_table
}

func set_dist_write_stats_openshift() []map[string]string {
	var dist_write_table []map[string]string
	m := make(map[string]string)
	// m["domain"] = fmt.Sprintf("%v",domain_flag)
	m["tag"] = "OpenShift"
	dist_write_table = append(dist_write_table, m)
	return dist_write_table
}

func set_dist_write_stats_ubuntu() []map[string]string {
	var dist_write_table []map[string]string
	m := make(map[string]string)
	// m["domain"] = fmt.Sprintf("%v",domain_flag)
	m["tag"] = "ubuntu"
	dist_write_table = append(dist_write_table, m)
	return dist_write_table
}

func set_dist_write_stats_k8osquery() []map[string]string {
	var dist_write_table []map[string]string
	m := make(map[string]string)
	// m["domain"] = fmt.Sprintf("%v",domain_flag)
	m["tag"] = "k8osquery"
	dist_write_table = append(dist_write_table, m)
	return dist_write_table
}

func set_dist_write_stats_yara() []map[string]string {
	var dist_write_table []map[string]string
	m := make(map[string]string)
	// m["domain"] = fmt.Sprintf("%v",domain_flag)
	m["tag"] = "uptycs_edr_linux_yara"
	dist_write_table = append(dist_write_table, m)
	return dist_write_table
}

func get_config_client(index int) *http.Client {
	return configClients[index]
}

func get_enroll_client(index int) *http.Client {
	return enrollClients[index]
}

func get_distributed_client(index int) *http.Client {
	return distReadClients[index]
}

func new_http_client(timeout time.Duration) *http.Client {
	client := &http.Client{
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{
				RootCAs:            caCertPool,
				InsecureSkipVerify: true,
			},
			DialContext: (&net.Dialer{
				Timeout:   120 * time.Second,
				KeepAlive: 0 * time.Second,
			}).DialContext,
		},
		Timeout: timeout,
	}
	return client
}

func set_http_clients() {
	for x := 0; x < count; x++ {
		e := new_http_client(time.Second * enrollReqTimeout)
		enrollClients = append(enrollClients, e)
		c := new_http_client(time.Second * enrollReqTimeout)
		configClients = append(configClients, c)
		l := new_http_client(time.Second * 180)
		logClients = append(logClients, l)
		if allow_reads {
			//r := new_http_client(time.Second * distributedDistInterval)
			r := new_http_client(time.Second * 120)
			distReadClients = append(distReadClients, r)
		}
	}
}

func init() {
	flag.Parse()
	if *domain_flag == "" || *secret_flag == "" || *name_flag == "" || *port_flag == "" || *count_flag == 0 {
		log.Fatalf("Please provide all flags of domain, secret, name, count, and port")
	}
	domain = *domain_flag
	secret = *secret_flag
	name = *name_flag
	port = *port_flag
	count = *count_flag
	enrollurl = fmt.Sprintf("https://%s.uptycs.net/agent/enroll", domain)
	configurl = fmt.Sprintf("https://%s.uptycs.net/agent/config", domain)
	logurl = fmt.Sprintf("https://%s.uptycs.net/agent/log", domain)
	distributedreadurl = fmt.Sprintf("https://%s.uptycs.net/agent/distributed_read", domain)
	distributedwriteurl = fmt.Sprintf("https://%s.uptycs.net/agent/distributed_write", domain)
	enrollReqTimeout = 30
	configInterval = 300
	distInterval = 200
	distributedDistInterval = 10

	//set_dist_write_stats()
	// disable logging
	gin.SetMode(gin.ReleaseMode)
	gin.DefaultWriter = ioutil.Discard
	set_log()
	parse_names()
	m := new(sync.Map)
	node_key = m
	num_log_channels = int(math.Ceil(float64(float64(count) / float64(assets_per_log_channel))))
	log.Println("Count:", count, "num_log_channels:", num_log_channels)

	for x := 0; x < num_log_channels; x++ {
		c := make(chan LogGoRoutineMsg)
		log_channels = append(log_channels, c)
		go log_msg_listener(c)
	}

	for x := 0; x < config_channel_count; x++ {
		c := make(chan ConfigRequest)
		config_channels = append(config_channels, c)
		go config_listener(c)
	}

	if allow_reads {
		//fmt.Println("dist_read_channel_count",dist_read_channel_count)
		for x := 0; x < dist_read_channel_count; x++ {
			c := make(chan DistReadRequest)
			//fmt.Println(x,"inside allow_reads",c)
			dist_read_channels = append(dist_read_channels, c)

			go dist_read_listener(c)
			//fmt.Println(x,"inside allow_reads",c,len(dist_read_channels))
		}
	}

	caCert, certErr := ioutil.ReadFile("ca.crt")
	if certErr != nil {
		log.Fatal(certErr)
	}
	caCertPool.AppendCertsFromPEM(caCert)
	set_http_clients()
}

func set_log() {
	logfile_name := "osx_log" + string(port) + ".out"
	os.Remove(logfile_name)
	logFile, err := os.OpenFile(logfile_name, os.O_CREATE|os.O_RDWR|os.O_APPEND, 0666)
	if err != nil {
		panic(err)
	}
	mw := io.MultiWriter(os.Stdout, logFile)
	log.SetOutput(mw)
}

func print_timers() {
	for {
		time.Sleep(time.Second * time.Duration(print_timer_sleep_time))
		print_timer("Enroll", enroll_fail_counter, enroll_histogram)
		print_timer("Config", config_fail_counter, config_histogram)
		print_timer("Log", log_fail_counter, log_histogram)
		print_timer("Distrubted_Read", dist_read_fail_counter, dist_read_histogram)
		print_timer("Distributed_Write", dist_write_fail_counter, dist_write_histogram)
		log.Println("Re-enrolled assets:", reenroll_count)
		log.Println("")
	}
}

func print_timer(name string, failed int, h Histogram) {
	log.Println("  ", name, "Failed:", failed, "Count:", len(h.Records), "Min:", h.min(), "Max:", h.max(),
		"Mean:", h.mean(), "Median:", h.median())
}

func main() {
	//defer profile.Start(profile.CPUProfile, profile.ProfilePath(".")).Stop()
	//go log.Println(http.ListenAndServe("localhost:8080", nil))
	go print_timers()
	gin.SetMode(gin.ReleaseMode)

	serv := gin.Default()
	//serv.Use(gzip.DefaultHandler().Gin)
	serv.POST("/", post_message)
	fmt.Println("Post", port)
	go serv.Run(":" + string(port))
	_, e := async.Concurrent(async.Tasks{
		func() int {
			time.Sleep(3 * time.Second)
			enroll()
			return 0
		},
	})

	if e != nil {
		fmt.Printf("Errors [%s]\n", e.Error()) // output errors separated by space
	}

}
