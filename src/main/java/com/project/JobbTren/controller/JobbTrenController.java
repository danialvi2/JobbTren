package com.project.JobbTren.controller;


import com.project.JobbTren.dto.AnalyzeResponse;
import com.project.JobbTren.service.JobbTrenService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.awt.*;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class JobbTrenController {

    private final JobbTrenService jobbTrenService;

    @PostMapping("/analyze")
    public ResponseEntity<?> analyze(
            @RequestPart("cv") MultipartFile cv,
            @RequestPart(value = "jobUrl") String jobUrl,
            @RequestPart(value = "projects") String projects){

        var response = jobbTrenService.sendToFlask("/analyze", cv, jobUrl, projects);
        return ResponseEntity.ok(response);
    }

    @PostMapping("/interview")
    public ResponseEntity<?> interview(
            @RequestPart(value = "cv", required = false) MultipartFile cv,
            @RequestParam(value = "jobUrl", required = false) String jobUrl,
            @RequestParam(value = "projects", required = false) String projects,
            @RequestPart(value = "level", required = false) String level
            ){
        System.out.println(">>> java recieved projects: " + projects);

        var response = jobbTrenService.sendToFlask("/interview", cv, jobUrl, projects, level);
        return ResponseEntity.ok(response);
    }


}
