/*
 * Copyright (c) 2020-2026 Karnak Team and other contributors.
 *
 * This program and the accompanying materials are made available under the terms of the Eclipse
 * Public License 2.0 which is available at https://www.eclipse.org/legal/epl-2.0, or the Apache
 * License, Version 2.0 which is available at https://www.apache.org/licenses/LICENSE-2.0.
 *
 * SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
 */
package org.karnak.backend.model.profilepipe;

import java.math.BigInteger;
import lombok.Getter;
import org.jspecify.annotations.NullUnmarked;
import org.weasis.core.util.StringUtil;
import org.weasis.dicom.util.Hmac;

/**
 * De-identification HMAC adding a {@link HashContext} on top of the weasis {@link Hmac}.
 */
@NullUnmarked
public class HMAC extends Hmac {

	@Getter
	private final HashContext hashContext;

	public HMAC(byte[] hmacKey) {
		super(hmacKey);
		this.hashContext = null;
	}

	public HMAC(HashContext hashContext) {
		super(hashContext.secret());
		this.hashContext = hashContext;
	}

	/**
	 * Keyed, non-reversible numeric pseudonym: the leading 8 bytes of
	 * HMAC-SHA256(secret, value) reduced modulo 10^digits and rendered as a zero-padded
	 * decimal string of exactly {@code digits} characters.
	 *
	 * <p>
	 * Deterministic for a given project secret and input. Used for CTP-style name
	 * hashing (mirrors CTP {@code @hash(this,10)} / {@code @hashname}), where the output
	 * must look like a numeric identifier rather than a DICOM UID.
	 * @param value input string, must be non-empty
	 * @param digits number of decimal digits to emit, 1..18
	 * @return a string of exactly {@code digits} decimal characters
	 */
	public String digitHash(String value, int digits) {
		if (!StringUtil.hasText(value)) {
			throw new IllegalArgumentException("digitHash: value must not be empty");
		}
		if (digits < 1 || digits > 18) {
			throw new IllegalArgumentException("digitHash: digits must be in 1..18");
		}
		final byte[] head = new byte[8];
		System.arraycopy(byteHash(value), 0, head, 0, 8);
		BigInteger n = new BigInteger(1, head).mod(BigInteger.TEN.pow(digits));
		return String.format("%0" + digits + "d", n);
	}

	/**
	 * Hides {@link Hmac#showHexKey(String)}, restoring the null/short-key guard that
	 * upstream dropped: callers (e.g. {@code SecretMapper}) pass whatever is stored, and
	 * a null or not-yet-generated (shorter than {@code KEY_BYTE_LENGTH * 2} hex chars)
	 * key must come back unchanged rather than throwing.
	 * @param key hexadecimal key, may be null or short
	 * @return the dashed-group representation, or {@code key} unchanged if it is null or
	 * too short
	 */
	public static String showHexKey(String key) {
		if (key == null || key.length() < KEY_BYTE_LENGTH * 2) {
			return key;
		}
		return Hmac.showHexKey(key);
	}

}
