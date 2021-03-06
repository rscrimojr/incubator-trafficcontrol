package api

/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"reflect"
	"testing"
)

func TestGetHandleErrorFunc(t *testing.T) {
	w := httptest.NewRecorder()
	r, err := http.NewRequest("", ".", nil)
	if err != nil {
		t.Error("Error creating new request")
	}
	body := `{"alerts":[{"text":"this is an error","level":"error"}]}`

	errHandler := GetHandleErrorFunc(w, r)
	errHandler(fmt.Errorf("this is an error"), http.StatusBadRequest)
	if w.Body.String() != body {
		t.Error("Expected body", body, "got", w.Body.String())
	}

	w = httptest.NewRecorder()
	body = `{"alerts":[]}`

	errHandler = GetHandleErrorFunc(w, r)
	errHandler(nil, http.StatusBadRequest)
	if w.Body.String() != body {
		t.Error("Expected body", body, "got", w.Body.String())
	}
}

func TestCreateAlerts(t *testing.T) {
	expected := Alerts{[]Alert{}}
	alerts := CreateAlerts(WarnLevel)
	if !reflect.DeepEqual(expected, alerts) {
		t.Errorf("Expected %v Got %v", expected, alerts)
	}

	expected = Alerts{[]Alert{Alert{"message 1", WarnLevel.String()}, Alert{"message 2", WarnLevel.String()}, Alert{"message 3", WarnLevel.String()}}}
	alerts = CreateAlerts(WarnLevel, "message 1", "message 2", "message 3")
	if !reflect.DeepEqual(expected, alerts) {
		t.Errorf("Expected %v Got %v", expected, alerts)
	}
}
