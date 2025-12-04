package com.project.JobbTren.service;


import com.fasterxml.jackson.databind.ObjectMapper;
import com.project.JobbTren.dto.AnalyzeResponse;
import com.project.JobbTren.dto.InterviewResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.client.WebClient;

import java.io.IOException;

@Service
public class JobbTrenService {

    private final WebClient webClient;

    public JobbTrenService(@Value("${flask.api.baseurl}") String flaskBaseUrl){
        this.webClient = WebClient.create(flaskBaseUrl);
    }

    public Object sendToFlask (String endpoint, MultipartFile cv, String jobUrl, String projects, String level){
        try {

        MultipartBodyBuilder bodyBuilder = new MultipartBodyBuilder();
        bodyBuilder.part("cv", new ByteArrayResource(cv.getBytes())).header("Content-Disposition", "form-data; name=cv; filename=" +cv.getOriginalFilename());
        bodyBuilder.part("jobUrl", jobUrl == null ? "" : jobUrl);
        bodyBuilder.part("projects", projects == null ? "" : projects);
        bodyBuilder.part("level", level != null ? level : "experienced");

        System.out.println(">>> jobUrl=" + jobUrl);

        String responseJson = webClient.post().uri(endpoint).contentType(MediaType.MULTIPART_FORM_DATA).bodyValue(bodyBuilder.build()).retrieve().bodyToMono(String.class).block();

        ObjectMapper mapper = new ObjectMapper();

        if (endpoint.equals("/analyze")) {
            return mapper.readValue(responseJson, AnalyzeResponse.class);
        } else if (endpoint.equals("/interview")) {
            return mapper.readValue(responseJson, InterviewResponse.class);
        } else {
            return responseJson;
        }

        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }
}
