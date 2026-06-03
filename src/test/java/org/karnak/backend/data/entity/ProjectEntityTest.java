/*
 * Copyright (c) 2024 Karnak Team and other contributors.
 *
 * This program and the accompanying materials are made available under the terms of the Eclipse
 * Public License 2.0 which is available at https://www.eclipse.org/legal/epl-2.0, or the Apache
 * License, Version 2.0 which is available at https://www.apache.org/licenses/LICENSE-2.0.
 *
 * SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
 */
package org.karnak.backend.data.entity;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class ProjectEntityTest {

	@Test
	void addActiveSecretEntity_sets_back_reference_on_secret() {
		ProjectEntity project = new ProjectEntity();
		project.setId(1L);
		byte[] key = new byte[16];
		SecretEntity secret = new SecretEntity(key);

		project.addActiveSecretEntity(secret);

		// The owning side of the @ManyToOne must point back to the project so
		// Hibernate writes a non-null project_id FK on insert.
		assertThat(secret.getProjectEntity())
			.as("secret.projectEntity must be set by addActiveSecretEntity (required for non-null project_id FK)")
			.isSameAs(project);
	}

	@Test
	void addActiveSecretEntity_activates_new_secret_and_deactivates_previous() {
		ProjectEntity project = new ProjectEntity();
		SecretEntity first = new SecretEntity(new byte[16]);
		project.addActiveSecretEntity(first);
		assertThat(first.isActive()).isTrue();

		SecretEntity second = new SecretEntity(new byte[16]);
		project.addActiveSecretEntity(second);

		assertThat(first.isActive()).isFalse();
		assertThat(second.isActive()).isTrue();
		assertThat(second.getProjectEntity()).isSameAs(project);
	}

	@Test
	void addActiveSecretEntity_second_secret_also_has_back_reference() {
		ProjectEntity project = new ProjectEntity();
		project.addActiveSecretEntity(new SecretEntity(new byte[16]));

		SecretEntity second = new SecretEntity(new byte[16]);
		project.addActiveSecretEntity(second);

		assertThat(second.getProjectEntity()).isSameAs(project);
	}

	@Test
	void retrieveActiveSecret_returns_the_most_recently_activated() {
		ProjectEntity project = new ProjectEntity();
		SecretEntity s1 = new SecretEntity(new byte[] { 1 });
		SecretEntity s2 = new SecretEntity(new byte[] { 2 });
		project.addActiveSecretEntity(s1);
		project.addActiveSecretEntity(s2);

		assertThat(project.retrieveActiveSecret()).isSameAs(s2);
	}

}
