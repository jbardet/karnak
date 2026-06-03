/*
 * Copyright (c) 2020-2021 Karnak Team and other contributors.
 *
 * This program and the accompanying materials are made available under the terms of the Eclipse
 * Public License 2.0 which is available at https://www.eclipse.org/legal/epl-2.0, or the Apache
 * License, Version 2.0 which is available at https://www.apache.org/licenses/LICENSE-2.0.
 *
 * SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
 */
package org.karnak.backend.service;

import java.util.List;
import java.util.Optional;
import org.karnak.backend.data.entity.DestinationEntity;
import org.karnak.backend.data.entity.ProjectEntity;
import org.karnak.backend.data.repo.DestinationRepo;
import org.karnak.backend.data.repo.ProjectRepo;
import org.karnak.backend.enums.NodeEventType;
import org.karnak.backend.model.event.NodeEvent;
import org.karnak.frontend.util.CollatorUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Project service
 */
@Service
public class ProjectService {

	// Repositories
	private final ProjectRepo projectRepo;

	private final DestinationRepo destinationRepo;

	// Event publisher
	private final ApplicationEventPublisher applicationEventPublisher;

	/**
	 * Autowired constructor
	 * @param projectRepo Project repository
	 * @param destinationRepo Destination repository
	 * @param applicationEventPublisher Application Event Publisher
	 */
	@Autowired
	public ProjectService(final ProjectRepo projectRepo, final DestinationRepo destinationRepo,
			final ApplicationEventPublisher applicationEventPublisher) {
		this.projectRepo = projectRepo;
		this.destinationRepo = destinationRepo;
		this.applicationEventPublisher = applicationEventPublisher;
	}

	/**
	 * Save in DB the project in parameter
	 * @param projectEntity Project to save
	 */
	public ProjectEntity save(ProjectEntity projectEntity) {
		return projectRepo.saveAndFlush(projectEntity);
	}

	/**
	 * Update project and destinations
	 * @param projectEntity Project to updated
	 */
	@Transactional
	public void update(ProjectEntity projectEntity) {
		if (projectEntity.getId() != null) {
			projectRepo.saveAndFlush(projectEntity);
			updateDestinations(projectEntity);
		}
	}

	/**
	 * Update destinations
	 * @param projectEntity Project destinations to update
	 */
	private void updateDestinations(ProjectEntity projectEntity) {
		for (DestinationEntity destinationEntity : projectEntity.getDestinationEntities()) {
			applicationEventPublisher.publishEvent(new NodeEvent(destinationEntity, NodeEventType.UPDATE));
		}
	}

	/**
	 * Remove project
	 * @param projectEntity Project to remove
	 */
	@Transactional
	public void remove(ProjectEntity projectEntity) {
		Long id = projectEntity.getId();
		// Clear FK references in destinations before deleting to avoid constraint violations.
		// Destinations using this project for de-identification or tag morphing become pass-through.
		for (DestinationEntity dest : destinationRepo.findByDeIdentificationProjectEntityId(id)) {
			dest.setDeIdentificationProjectEntity(null);
			destinationRepo.save(dest);
		}
		for (DestinationEntity dest : destinationRepo.findByTagMorphingProjectEntityId(id)) {
			dest.setTagMorphingProjectEntity(null);
			destinationRepo.save(dest);
		}
		projectRepo.deleteById(id);
		projectRepo.flush();
	}

	/**
	 * Retrieve all projects
	 * @return projects found
	 */
	public List<ProjectEntity> getAllProjects() {
		List<ProjectEntity> projects = projectRepo.findAll();
		projects.sort(CollatorUtils.comparing(ProjectEntity::getName));
		return projects;
	}

	/**
	 * Retrieve project by id
	 * @param id Id to look for
	 * @return project found
	 */
	public ProjectEntity retrieveProject(Long id) {
		ProjectEntity projectEntity = null;
		if (id != null) {
			Optional<ProjectEntity> projectEntityOptional = projectRepo.findById(id);
			if (projectEntityOptional.isPresent()) {
				projectEntity = projectEntityOptional.get();
			}
		}
		return projectEntity;
	}

}
