/**
 * KOI bootstrap
 *
 * Copyright (c) 2012 Knewton
 * Dual licensed under:
 *  MIT: http://www.opensource.org/licenses/mit-license.php
 *  GPLv3: http://www.opensource.org/licenses/gpl-3.0.html
 */
/*jslint regexp: true, browser: true, maxerr: 50, indent: 4, maxlen: 79 */
(function () {
	"use strict";

	Screw.Unit(function () {
		describe("bootstrapping", function () {
			it("should complete loading successfully", function () {
				expect(window.__bootstrapped__).to(be_true);
			});
			it("should handle application css includes", function () {
				expect($("#red-test-box").css("backgroundColor"))
					.to(equal, "rgb(255, 0, 0)");
			});
			it("should handle application script includes", function () {
				expect(window.__included_script__).to(be_true);
			});
			it("should handle component replacements", function () {
				// This is the structure we expect the HTML to have after
				// component processing has finished.
				expect($("#html2")).to(have_length, 1);
				expect($(".foo", "#html2")).to(have_length, 1);
				expect($(".bar", "#html2")).to(have_length, 1);
				expect($("#html1", "#html2")).to(have_length, 1);
				expect($("#baz", "#html1")).to(have_length, 1);
			});
		});
	});

}());

