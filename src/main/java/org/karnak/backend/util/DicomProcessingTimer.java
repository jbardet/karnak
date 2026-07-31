/*
 * Copyright (c) 2021 Karnak Team and other contributors.
 *
 * This program and the accompanying materials are made available under the terms of the Eclipse
 * Public License 2.0 which is available at https://www.eclipse.org/legal/epl-2.0, or the Apache
 * License, Version 2.0 which is available at https://www.apache.org/licenses/LICENSE-2.0.
 *
 * SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
 */
package org.karnak.backend.util;

import lombok.extern.slf4j.Slf4j;

import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Utility class for timing DICOM processing phases.
 * Tracks timing for: DICOM file reading, processing through Karnak, and writing to destination.
 */
@Slf4j
public class DicomProcessingTimer {
    
    public enum Phase {
        DICOM_READ("DICOM_READ"),
        KARNAK_PROCESS("KARNAK_PROCESS"), 
        DICOM_WRITE("DICOM_WRITE"),
        TOTAL_PROCESSING("TOTAL_PROCESSING");
        
        private final String name;
        
        Phase(String name) {
            this.name = name;
        }
        
        public String getName() {
            return name;
        }
    }
    
    private static final ConcurrentHashMap<String, TimingContext> timingContexts = new ConcurrentHashMap<>();
    
    public static class TimingContext {
        private final String sopInstanceUID;
        private final ConcurrentHashMap<Phase, Long> startTimes = new ConcurrentHashMap<>();
        private final ConcurrentHashMap<Phase, Long> durations = new ConcurrentHashMap<>();
        private final AtomicLong totalStartTime = new AtomicLong();
        
        public TimingContext(String sopInstanceUID) {
            this.sopInstanceUID = sopInstanceUID;
            this.totalStartTime.set(System.nanoTime());
        }
        
        public String getSopInstanceUID() {
            return sopInstanceUID;
        }
        
        public void startPhase(Phase phase) {
            startTimes.put(phase, System.nanoTime());
            log.info("TIMING: [{}] Starting phase {} at {}", sopInstanceUID, phase.getName(), System.currentTimeMillis());
        }
        
        public void endPhase(Phase phase) {
            Long startTime = startTimes.get(phase);
            if (startTime != null) {
                long duration = System.nanoTime() - startTime;
                durations.put(phase, duration);
                double durationMs = duration / 1_000_000.0;
                log.info("TIMING: [{}] Completed phase {} in {:.2f} ms", sopInstanceUID, phase.getName(), durationMs);
            } else {
                log.warn("TIMING: [{}] Attempted to end phase {} without starting it", sopInstanceUID, phase.getName());
            }
        }
        
        public void logFinalTiming() {
            long totalDuration = System.nanoTime() - totalStartTime.get();
            double totalMs = totalDuration / 1_000_000.0;
            
            StringBuilder summary = new StringBuilder();
            summary.append(String.format("TIMING_SUMMARY: [%s] Total: %.2f ms", sopInstanceUID, totalMs));
            
            for (Phase phase : Phase.values()) {
                if (phase != Phase.TOTAL_PROCESSING && durations.containsKey(phase)) {
                    double phaseMs = durations.get(phase) / 1_000_000.0;
                    summary.append(String.format(" | %s: %.2f ms", phase.getName(), phaseMs));
                }
            }
            
            log.info(summary.toString());
        }
        
        public double getPhaseDurationMs(Phase phase) {
            Long duration = durations.get(phase);
            return duration != null ? duration / 1_000_000.0 : 0.0;
        }
    }
    
    /**
     * Start timing for a DICOM instance
     */
    public static TimingContext startTiming(String sopInstanceUID) {
        TimingContext context = new TimingContext(sopInstanceUID);
        timingContexts.put(sopInstanceUID, context);
        log.info("TIMING: [{}] Started timing for DICOM instance", sopInstanceUID);
        return context;
    }
    
    /**
     * Get existing timing context for a DICOM instance
     */
    public static TimingContext getContext(String sopInstanceUID) {
        return timingContexts.get(sopInstanceUID);
    }
    
    /**
     * Start a specific phase for a DICOM instance
     */
    public static void startPhase(String sopInstanceUID, Phase phase) {
        TimingContext context = timingContexts.get(sopInstanceUID);
        if (context != null) {
            context.startPhase(phase);
        } else {
            log.warn("TIMING: [{}] No timing context found when starting phase {}", sopInstanceUID, phase.getName());
        }
    }
    
    /**
     * End a specific phase for a DICOM instance
     */
    public static void endPhase(String sopInstanceUID, Phase phase) {
        TimingContext context = timingContexts.get(sopInstanceUID);
        if (context != null) {
            context.endPhase(phase);
        } else {
            log.warn("TIMING: [{}] No timing context found when ending phase {}", sopInstanceUID, phase.getName());
        }
    }
    
    /**
     * Complete timing for a DICOM instance and log final summary
     */
    public static void completeTiming(String sopInstanceUID) {
        TimingContext context = timingContexts.remove(sopInstanceUID);
        if (context != null) {
            context.logFinalTiming();
        } else {
            log.warn("TIMING: [{}] No timing context found when completing timing", sopInstanceUID);
        }
    }
    
    /**
     * Clean up timing context without logging (in case of errors)
     */
    public static void cleanupTiming(String sopInstanceUID) {
        TimingContext context = timingContexts.remove(sopInstanceUID);
        if (context != null) {
            log.debug("TIMING: [{}] Cleaned up timing context", sopInstanceUID);
        }
    }
    
    /**
     * Get current number of active timing contexts (for monitoring)
     */
    public static int getActiveContextCount() {
        return timingContexts.size();
    }
}
